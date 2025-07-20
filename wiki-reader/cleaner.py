import re

class Cleaner:
    # stop words to remove
    _to_remove_from_tags = {'in', 'on', 'at', 'to', 'of', 'from', 'into', 'through', 'by', 'like', 'for', 'and', 'the', 'a', 'an'}

    # left right pairs of files, citations, Wikitext markup, etc. to need to be removed
    bracket_pairs = {'{{': '}}', '[[': ']]', '<!': '!>'}

    def __init__(self, ):
        to_remove = ([
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
            r"<math>.*?</math>",            # remove equations and code blocks
            r"<code.*?</code>"
        ])
        remove_string = r"(" + r"|".join(to_remove)+r")"
        self.remove_regex = re.compile(remove_string, flags = re.DOTALL)
        
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
        
        self.stop_reading_regex = re.compile(r"={2,}\s?(See also|Notes|References|Further reading|External links)", flags= re.DOTALL)
        
        self.links_regex = re.compile(r"\[\[(?!(File|Image):).*?\]\]", flags= re.DOTALL)
        
        self.section_regex = re.compile(r"(={2,}.*?={2,}\s?\n{1,}){1,}(\{\{(Main|Further)\|(.*?)\}\})?")
        
    @staticmethod
    def make_section_tags(match: re.Match) -> str:
        match_text = match.group()
        i = match_text.find('{{')
        if i != -1:
            j = match_text.find('|', i)
            match_text = match_text[:i] + match_text[j+1:-2]
        match_text = match_text.replace('=', '').replace('\n',' ').replace(',', '').replace("'","").lower()
        out = ["##tags:"]
        out.append(match_text)
        out.append('\n\n')
        return ' '.join(out)
    
    def make_intro_section(self, text) -> None:
        tags = set()
        i = -2
        out = ["##tags:"]
        if text.startswith("{{Short description|"):
            i = text.find('}}')
            tags = [word for word in text[20:i].replace('|', ' ').split()]
        out.extend(tags)
        out.append('\n\n')
        out = ' '.join(out)
        text = out + text[i+2:]
        return text
            
    def generate_section_tags(self, text) -> None:
        text = self.make_intro_section(text)
        return self.section_regex.sub(Cleaner.make_section_tags, text)
    
    def remove_references_section(self, text: str) -> None:
        match = self.stop_reading_regex.search(text)
        if match:
            return text[:match.start()]
        return text
    
    @staticmethod
    def _replace_link(match: re.Match) -> str:
        """
        inter wiki links have the form: 
            case 1: [link page]]
            case 2: [[link page|display text]]
        """
        text = match.group()
        j = text.find('|')
        if j == -1:
            return text[2:-2]    # case 1: return link page
        else:
            return text[j+1:-2]  # case 2: return display text
    
    def cleanup_links(self, text: str) -> str:
        return self.links_regex.sub(Cleaner._replace_link, text)
    
    def remove_non_nested_elements(self, text):
        return self.remove_regex.sub("", text)
    
    def remove_nested_elements(self, text):
        new_text = []
        open_brackets = 0
        left_bracket, right_bracket = None, None
        for line in text.split('\n'):
            new_line = []
            for token in line.split():
                if open_brackets > 0:
                    if token == left_bracket:
                        open_brackets += 1
                    elif token == right_bracket:
                        open_brackets -= 1
                    if open_brackets == 0:
                        left_bracket = right_bracket = None
                elif token in Cleaner.bracket_pairs:
                    left_bracket, right_bracket = token, Cleaner.bracket_pairs[token]
                    open_brackets = 1
                else:
                    new_line.append(token)
            new_line.append('\n')  # keep original line spacing
            new_line = ' '.join(new_line)
            new_text.append(new_line)
        return ''.join(new_text)
    
    def tokenize(self, text):
        text = text.replace('|}}', '| }}').replace('{|', '<!').replace('|}', '!>')
        return self.lexer_regex.sub(lambda x: " "+x.group()+" ", text)
    
    def finalize(self, text: str) -> str:
        text = re.sub(r"({{|}}|\||\t{2, }|\(\s*\)|\(\s*;\s*\)|\s*;\s*)", ' ', text)
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        return text
    
    def clean_text(self, text):
        text = self.remove_references_section(text)
        text = self.cleanup_links(text)
        text = self.remove_non_nested_elements(text)
        # must remove non nested elements first because some section headings contain html and other styling
        text = self.generate_section_tags(text)
        text = self.tokenize(text)
        text = self.remove_nested_elements(text)
        text = self.finalize(text)
        return text
        
                    
        
        
    
    
