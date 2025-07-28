import re

class Cleaner:
    '''
    cleans text from wikipedia xml dumps
    '''
    
    # the left and right indicator pairs of wikitext markup 
    # e.g., {{InfoBox ...}}, or [[File: ...]]
    bracket_pairs = {'{{': '}}', '[[': ']]', '<!': '!>'}

    def __init__(self, ):
        # regex to remove simple objects and formating
        to_remove = [
            r"<!--.*?-->",                  # remove comments
            r"</?nowiki>",
            r"<ref[^(/>)]*>.*?</ref>",      # remove references
            r"<ref.*?/>",                  
            r"</?span[^>]*>",               # remove html and wikitext font styling
            r"<br\s*/?>",
            r"</?div[^>]*>",
            r"</?su(p|b)>",
            r"</?u>",
            r"'{2,}",
            r"</?blockquote>",
            r"&nbsp;",
            r"</?small>",
            r"<gallery[^>]*>.*?</gallery>", # remove collections of images
            r"<imagemap.*?</imagemap>",
            r"<math.*?</math>",             # remove equations and code blocks
            r"<code.*?</code>"
        ]
        remove_string = r"(" + r"|".join(to_remove)+r")"
        self.remove_regex = re.compile(remove_string, flags = re.DOTALL)
        
        # regex to add spaces around the start and end of wikitext markup
        # e.g., [[File: file_name]] -> [[ File: file_name ]]
        # simplifies removing these elements later
        remaining_tokens = ([
            r"{{",
            r"}}",
            r"\[\[",
            r"\]\]",
            r"<!",                        # replacement for {| and |}
            r"!>"
        ])
        token_string = r"(" + r"|".join(remaining_tokens)+r")"
        self.lexer_regex = re.compile(token_string, flags = re.DOTALL)
        
        # regex to find any of the following sections:
        #   See also, Notes, Refereneces, Further reading, External links
        # text will be cutoff at first of these sections (if any)
        self.stop_reading_regex = re.compile(r"={2,}\s?(See also|Notes|References|Further reading|External links)", flags= re.DOTALL)
        
        # regex to find interwiki links
        self.links_regex = re.compile(r"\[\[(?!(File|Image):).*?\]\]", flags= re.DOTALL)
        
        # regex to find sections and associated links
        self.section_regex = re.compile(r"(={2,}.*?={2,}\s?\n{1,}){1,}(\{\{(Main|Further)\|(.*?)\}\})?")
        
    @staticmethod
    def make_section_tags(match: re.Match) -> str:
        '''
        Extracts section name and any links. For example, match_text:
            == Section_Name ==
            {{Main/Further| link_1, link_2, ..., link_n}}
            
        converts to:
            !!tags: Section_Name link_1 link_2 ... link_n
        '''
        match_text = match.group()
        i = match_text.find('{{') # check if there are any links
        if i != -1:
            j = match_text.find('|', i) 
            # flattened, the match text is:
            # == Section_Name == {{Further | link_1, link_2, ..., link_n}}
            #                    i         j
            # <- match_text[:i]->            <---  match_text[j+1:-2] ->
            match_text = match_text[:i] + match_text[j+1:-2]
        match_text = match_text.replace('=', '').replace('\n',' ').replace(',', '').replace("'","").lower()
        out = ["!!tags:"]
        out.append(match_text)
        out.append('\n\n')
        return ' '.join(out)
    
    def make_intro_section(self, text: str) -> None:
        tags = set()
        i = -2
        out = ["!!tags:"]
        if text.startswith("{{Short description|"):
            i = text.find('}}')
            # the lengrh of {{Short descriotion| is 20 characters
            tags = [word for word in text[20:i].replace('|', ' ').split()]
        out.extend(tags)
        out.append('\n\n')
        out = ' '.join(out)
        text = out + text[i+2:]
        return text
            
    def generate_section_tags(self, text) -> None:
        '''
        condenses section name and links, refer to make_sction_tags for example
        '''
        text = self.make_intro_section(text)
        return self.section_regex.sub(Cleaner.make_section_tags, text)
    
    def remove_references_section(self, text: str) -> None:
        '''
        removes text starting from any of these sections:
            See also, Notes, Refereneces, Further reading, External links
        '''
        match = self.stop_reading_regex.search(text)
        if match:
            return text[:match.start()]
        return text
    
    @staticmethod
    def _replace_link(match: re.Match) -> str:
        """
        inter wiki links have the form: 
            case 1: [[link page]]
            case 2: [[link page|display text]]
        """
        text = match.group()
        j = text.find('|')
        if j == -1:
            return text[2:-2]    # case 1: return link page
        else:
            return text[j+1:-2]  # case 2: return display text
    
    def cleanup_links(self, text: str) -> str:
        # see above
        return self.links_regex.sub(Cleaner._replace_link, text)
    
    def remove_non_nested_elements(self, text: str) -> str:
        ''' 
        remove markup and simple objects that are not nested within each other
        '''
        return self.remove_regex.sub("", text)
    
    def remove_nested_elements(self, text: str) -> str:
        '''
        remove infoboxes, tables, and other nested elements that start/stop 
        with brackets: {{, }}, [[, ]], {|, |}
        '''
        '''
        Example:
            
        {{Infobox person                    # open_brackets = 1 (remove all text until closing this bracket)
           name = "Alice"
           friend = "Bob"
           {{list                           # open_brackets = 2
              list item_1 [[some file]]     # only count brackets of the outer most type: {{ and }} in this example
              list item_2 
              {{list                        # open_brackets = 3
                 sublist item 1
                 sublist item 2
              }}                            # open_brackets = 2
           }}                               # open_brackets = 1
        }}                                  # open_brackets = 0 (can write text after this)
        '''
        '''
        tables start/end with {| ... |}
        some elements allow for pipes with no right hand side arguement,
        e.g., {{this is not a table|}}
        therefore, replace |}} with | }} to distinguish these elements 
        from the end of a table
        '''
        new_text = []
        open_brackets = 0
        # start/end indicator for nested element to remove
        left_bracket, right_bracket = None, None
        for line in text.split('\n'):
            new_line = []
            # lines starting with *, #, or : are lists, 
            # see https://en.wikipedia.org/wiki/Help:List
            if line and line[0] in '*#:': 
                continue 
            for token in line.split():
                if open_brackets > 0:
                    # removing a nested element so no words are written
                    # only track changes in number of open brackets
                    if token == left_bracket:
                        open_brackets += 1
                    elif token == right_bracket:
                        open_brackets -= 1
                    if open_brackets == 0:
                        # finished removing the nested element
                        # now we can write words again
                        left_bracket = right_bracket = None
                elif token in Cleaner.bracket_pairs:
                    # start of new nested element to remove
                    left_bracket, right_bracket = token, Cleaner.bracket_pairs[token]
                    open_brackets = 1
                else:
                    new_line.append(token)
            # extra \n keeps original line spacing between paragraphs
            # useful if you want to separate text into paragraphs
            new_line.append('\n')  
            new_line = ' '.join(new_line)
            new_text.append(new_line)
        return ''.join(new_text)
    
    def tokenize(self, text: str) -> str:
        ''' 
        add spaces around start and end indicators of wikitext markup
        '''
        text = text.replace('|}}', '| }}').replace('{|', '<!').replace('|}', '!>')
        return self.lexer_regex.sub(lambda x: " "+x.group()+" ", text)
    
    def finalize(self, text: str) -> str:
        '''
        Remove extra spaces, newlines, empty paratheses, etc. created by deleting markup.
        Tokenizers with ignore extra spaces anyway so this mostly for readability
        '''
        text = re.sub(r"({{|}}|\||\t{2, }|\(\s*\)|\(\s*;\s*\)|\s*;\s*)", ' ', text)
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        return text
    
    def clean_text(self, text: str) -> str:
        ''' 
        Extracts cleaned text from raw xml text
        '''
        text = self.remove_references_section(text)
        text = self.cleanup_links(text)
        text = self.remove_non_nested_elements(text)
        # must remove non nested elements because some section headings contain html and other styling
        text = self.generate_section_tags(text)
        text = self.tokenize(text)
        text = self.remove_nested_elements(text)
        text = self.finalize(text)
        return text
