export async function getDocuments(question, searchType) {
    const query = "question="+question+"&search_type="+searchType
    //const url = "http://3.149.123.81:8000/ask?question="+question;
    const url = "http://127.0.0.1:8000/ask?"+query
    try {
        //alert(url)
        const response = await fetch(url);
        if (!response.ok) {
          //alert('response not okay?!')
          throw new Error(`Response status: ${response.status}`);
        }
        
        //alert('recieved info')
        const json = await response.json();
        //alert(JSON.stringify(json, null, 2));
        var arr = Array.from(json);
        let c = 0.0; // c = 0.1
        for(let i = 0; i < arr.length; i++) {
            arr[i].score = (1-c)*arr[i].HNSW_score + c*arr[i].QA_score;
        }
        arr.sort((a,b) => b.score-a.score);
        //alert(arr);
        return arr;
    } catch (error) {
        alert('something wrong')
        console.error(error.message);
    }
}