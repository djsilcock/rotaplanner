
export const recalculate = async (startDate) => {

    const it = fetch('/backend/recalculate', {
        headers: { 'accept': 'application/json' },
        method: 'post',
        body: JSON.stringify({startDate})
    });
    
    
};

