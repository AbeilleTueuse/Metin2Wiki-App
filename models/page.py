from typing import Any, Literal
import mwparserfromhell


class Page:


    def __init__(
            self,
            mediawiki,
            title: str | None = None,
            pageid: int | None = None,
            content = None,
            parse = False
            ):

        self.mediawiki = mediawiki
        self.title = title
        self.pageid = pageid
        self.content = self._parse(content, parse)


    def __str__(self):

        return f'(Page: [name: {self.title}, content: {self.content}])'


    def __eq__(self, __value):
        if self.pageid is not None and isinstance(__value, Page):
            return self.pageid == __value.pageid
        return False
    

    def _parse(self, content, parse):
        if content is not None:
            if parse:
                return mwparserfromhell.parse(content)
            return content
        

    @property
    def backlinks(self):

        query_params = {
            'action': 'query',
            'format': 'json',
            'list': 'backlinks',
            'bllimit': 'max'
        }

        if self.title is not None:
            query_params['bltitle'] = self.title
        else:
            query_params['blpageid'] = self.pageid

        request_result = self.mediawiki.wiki_request(query_params)
        pages = request_result['query']['backlinks']

        return [Page(self, page['title'], page['pageid'])  for page in pages]
    

    def get_content(self, parse = False):

        if self.content is not None:
            return

        query_params = {
            'action': 'query',
            'format': 'json',
            'prop': 'revisions',
            'rvprop': 'content',
            'formatversion': '2',
        }

        if self.pageid is not None:
            query_params['pageids'] = str(self.pageid)
        elif self.title is not None:
            query_params['titles'] = str(self.title)
        else:
            raise ValueError()

        request_result = self.mediawiki.wiki_request(query_params)
        content = request_result['query']['pages'][0]['revisions'][0]['content']

        self.content = self._parse(content, parse)


    def write(self, summary = ''):
        
        self.mediawiki.edit(page = self, summary = summary)


    def delete(self, reason = ''):
    
        self.mediawiki.delete(page = self, reason = reason)


    def get_parameters(self, template):

        return [param.name for param in template.params]


    def add_parameter(self, template, parameter_name: str, parameter_value: str, before: str | None = None):

        if not template.has(parameter_name):
            template.add(parameter_name, parameter_value, before = before)


    def change_parameter_name(self, template, parameter_name: str, new_parameter_name: str):

        if template.has(parameter_name) and not template.has(new_parameter_name):
            template.get(parameter_name).name = new_parameter_name


    def change_parameter_value(self, template, parameter_name: str, new_parameter_value: str):

        if template.has(parameter_name):
            template.get(parameter_name).value = new_parameter_value


    def delete_parameter(self, template, parameter_name: str):

        if template.has(parameter_name):
            template.remove(parameter_name)


    def match_template(self, template, template_name: str) -> bool:

        return template.name.matches(template_name)
    

    def change_text(self, text_to_change, new_text):

        self.content = self.content.replace(text_to_change, new_text)


class EntityPage(Page):


    def __init__(
            self,
            page: Page,
            entity: Literal['Monstres', 'Metin'] = 'Monstre'
            ):
        
        super().__init__(
            mediawiki = page.mediawiki,
            title = page.title,
            pageid = page.pageid,
            content = page.content
        )
        self.page = page
        self.entity = entity
        self.template = self._check_template()
        self.vnum = self._get_vnum()


    def _check_template(self):

        if self.content is None:
            self.get_content(parse = True)

        if not isinstance(self.content, mwparserfromhell.wikicode.Wikicode):
            self.content = self._parse(self.content, True)

        template = self.content.filter_templates()[0]
        if template.name.matches(self.entity):
            return template
        else:
            raise ValueError(f"{self.page.title} doesn't have {self.entity} template.")
        

    def _get_vnum(self):

        code = self.template.get('Code').value
        code = str(code).strip()

        return self.mediawiki.code_to_vnum(str(code))
    

    def get_parameters(self):
        return super().get_parameters(self.template)
    

    # def get_proto_values(self):

    #     values = {parameter: str(self.template.get(parameter).value).strip() for parameter in self.PROTO_PARAMETERS['obligatory']}
    #     values['Agressif'] = values['Agressif'].replace('NO', 'N')
    #     if self.template.has('Nom'):
    #         values['Nom'] = str(self.template.get('Nom').value).strip()
    #     else:
    #         if not self.name.endswith('(quête)'):
    #             values['Nom'] = self.name.split(' (')[0]
    #         else:
    #             values['Nom'] = self.name

    #     if self.template.has('Élément2'):
    #         values['Élément'] += f'|{str(self.template.get("Élément2").value).strip()}'

    #     if self.template.has('PM'):
    #         values['PM'] = str(self.template.get('PM').value).strip()

    #    return values
    

    # def compare_with_proto(self, proto):

    #     proto_values = self.get_proto_values()
    #     proto_true = proto.loc[self.vnum]

    #     for parameter_name in proto_values:
    #         if proto_values[parameter_name] != proto_true[parameter_name]:
    #             print(f'Monster: {self.name} ({self.vnum}), error: {parameter_name} ({proto_values[parameter_name]} instead of {proto_true[parameter_name]})')

    #     if (proto_true['PM']) != '0' or ('PM' in proto_values):
    #         if proto_true['PM'] != proto_values['PM']:
    #             print(f'Monster: {self.name} ({self.vnum}), error: PM ({proto_values["PM"]} instead of {proto_true["PM"]})')

    
    def add_parameter(self, parameter_name: str, parameter_value: str, before: str | None = None):
        return super().add_parameter(self.template, parameter_name, parameter_value, before)
    

    def change_parameter_name(self, parameter_name: str, new_parameter_name: str):
        return super().change_parameter_name(self.template, parameter_name, new_parameter_name)
    

    def change_parameter_value(self, parameter_name: str, new_parameter_value: str):
        return super().change_parameter_value(self.template, parameter_name, new_parameter_value)
    

    def delete_parameter(self, parameter_name: str):
        return super().delete_parameter(self.template, parameter_name)
    

class MonsterPage(EntityPage):
            

    def __init__(
            self,
            page: Page
            ):

        super().__init__(
            page = page,
            entity = 'Monstres'
        )


class MetinPage(EntityPage):
            

    def __init__(
            self,
            page: Page
            ):

        super().__init__(
            page = page,
            entity = 'Metin'
        )


class Pages:


    def __init__(
            self,
            mediawiki,
            data: list[int] | list[Page]
            ):

        self.mediawiki = mediawiki
        self.data = self.mediawiki._check_params(data, type_ = 'ids')


    def content(self, parse = False):

        def create_page(page_data):

            page = Page(
                mediawiki = self.mediawiki,
                title = page_data['title'],
                pageid = page_data['pageid'],
                content = page_data['revisions'][0]['content'],
                parse = parse
            )

            return page

        query_params = {
            'action': 'query',
            'format': 'json',
            'prop': 'revisions',
            'rvprop': 'content',
            'formatversion': '2',
        }

        result = []

        for pages in self.data:

            query_params['pageids'] = '|'.join(map(str, pages))
            request_result = self.mediawiki.wiki_request(query_params)
            result += request_result['query']['pages']

        return [create_page(page_data) for page_data in result]
    

if __name__ == '__main__':

    pages = Pages(0, ['0', '1', '2'])
    print(pages.data)
    print(pages.data[2].pageid)