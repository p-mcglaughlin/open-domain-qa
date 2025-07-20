import { useState } from "react";

export function DropdownMenu( {onSelectAction} ) {
    const [isOpen, setIsOpen] = useState(false);
    const search_types = [
        'vector and fulltext', 
        'vector only',
        'fulltext only'
    ]

    const handleToggle = () => { setIsOpen(!isOpen); };
    const handleSelect = (type) => { onSelectAction(type); setIsOpen(false); }

    return (
        <>
        <button onClick={handleToggle} class='dropdown-trigger'>
            ☰ {isOpen && 'search type'}
        </button>
        {isOpen && (
            <ul class='no-bullets'>
                {search_types.map((type) => (
                    <li class='dropdown-menu' key={type} onClick={() => handleSelect(type) }>
                        {type}
                    </li>
                ))}
            </ul>
        )}
        </>
    );
}