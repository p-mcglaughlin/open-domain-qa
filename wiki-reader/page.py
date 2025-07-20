class Page:
    '''
    struct for Wikipedia articles
    '''
    def __init__(self, page_id: int, title: str, text: str):
        self.page_id = page_id
        self.title = title
        self.text = text
        
