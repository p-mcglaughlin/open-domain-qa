export async function getDocuments(question, searchType) {
    const query = "question="+question+"&search_type="+searchType
    const url = "http://127.0.0.1:8000/ask?"+query
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
        
        const json = await response.json();
        var arr = Array.from(json);
        return arr;
    } catch (error) {
        alert('something wrong')
        console.error(error.message);
    }
}
