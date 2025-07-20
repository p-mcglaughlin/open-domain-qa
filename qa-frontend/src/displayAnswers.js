import { useState } from 'react';

export function ShowAnswer({doc}) {
  const [showMore, setShowMore] = useState(false);

  function handleMoreClick() {
    setShowMore(!showMore);
  }

  const ans = doc.ans;
  const text = doc.text;
  const i = text.indexOf(ans);
  const j = i+ans.length;
  const shortStart = i===0? '' : '...'+text.slice(Math.max(0,i-50), i);
  const shortEnd = text.slice(j, Math.min(text.length, j+50))+'...';
  const fullStart = i===0? '' : text.slice(0, i);
  const fullEnd = text.slice(j, text.length);
  const title = doc.title;
  const source_url = 'https://www.wikipedia.org'+doc.href+ '#:~:text='+doc.ans;
  const full_score = 100*doc.score
  const score = full_score.toFixed(2)
  return (
    <div class='answer'>
        <b>{ans}</b>
        <br />
        confidence: {score}, source article: <a href={source_url}>{title}</a>
        {'  '}
        <button class='expand_button' onClick={handleMoreClick}>
          {showMore? '-': '+'}
        </button>
        <br />
        {showMore? fullStart: shortStart} <b>{ans}</b> {showMore? fullEnd: shortEnd}
    </div>
  );
}

export function ShowAnswerList({answers}) {
  var copies = Array.from(answers);
  let ansList = copies.map(ans => <li><ShowAnswer doc = {ans} /> </li>);
  return <ul>{ansList}</ul>;
}