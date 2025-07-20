import { useState, useRef } from 'react';
import { getDocuments } from './fetchDocuments.js';
import { ShowAnswerList } from './displayAnswers.js';
import { DropdownMenu } from './settingsMenu.js';
import './App.css';

function App() {
  const [docs, setDocs] = useState([]);
  const [searchType, setSearchType] = useState('VEC_FT');
  const questionRef = useRef(null);

  async function handleKeyDown(e) {
    if(e.key === "Enter") {
      e.preventDefault();
      document.body.style.cursor = 'wait';
      const question = questionRef.current.value;
      if (question !== '') {
        const relevantDocs = await getDocuments(question, searchType);
        setDocs(relevantDocs);
      }
      document.body.style.cursor = 'default';
    }
  }

  function handleSelect(type) {
    let selected = 'VEC_FT';
    if(type === "vector only") {
      selected = 'VEC';
    }
    else if(type === 'fulltext only') {
      selected = 'FT';
    }
    setSearchType(selected);
  }

  return (
    <>
      <div >
          <h2 class="questionArea">open domain question answering</h2>
          <div style={{display:'flex', alignItems:'flex-start'}}>
            <textarea 
              class = "textInput"
              name = "question"
              defaultValue = "Ask a trivia question..."
              rows = {2}
              cols = {60}
              onKeyDown = {handleKeyDown}
              ref = {questionRef}
            />
            <DropdownMenu onSelectAction = {handleSelect} />
          </div>
          <hr />
      </div>
      <div className="answerArea">
        <ShowAnswerList answers={docs} />
      </div>
    </>
  );
}

export default App;
