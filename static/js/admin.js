document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.prize-cell').forEach(cell => {
        const score = cell.getAttribute('data-score');
        cell.innerText = PrizeManager.getPrizeName(score);
    });
});

async function executeAdminQuery() {
    const query = document.getElementById('query-input').value;
    const res = await fetch('/admin/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: query})
    });
    const result = await res.json();

    if (result.error) {
        alert(result.error);
        return;
    }

    let html = '<table border="1" style="width:100%; border-collapse:collapse;"><thead><tr>';
    result.columns.forEach(col => html += `<th>${col}</th>`);
    html += '</tr></thead><tbody>';
    result.data.forEach(row => {
        html += '<tr>';
        result.columns.forEach(col => html += `<td>${row[col]}</td>`);
        html += '</tr>';
    });
    html += '</tbody></table>';
    document.getElementById('query-result').innerHTML = html;
}

document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.prize-cell').forEach(cell => {
        const score = cell.getAttribute('data-score');
        if(score) cell.innerText = PrizeManager.getPrizeName(score);
    });
});

// 발송 처리
function processSend(userId) {
    if(!confirm("상품을 발송 처리하시겠습니까?")) return;
    fetch(`/admin/send-product/${userId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if(data.success) {
                document.getElementById(`btn-send-${userId}`).style.display = 'none';
                document.getElementById(`btn-cancel-${userId}`).style.display = 'inline-block';
                const status = document.getElementById(`status-${userId}`);
                status.innerText = '발송완료';
                status.className = 'status-badge status-y';
            } else { alert(data.message); }
        });
}

// 취소 처리
function processCancel(userId) {
    if(!confirm("발송을 취소하시겠습니까?")) return;
    fetch(`/admin/cancel-product/${userId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if(data.success) {
                document.getElementById(`btn-cancel-${userId}`).style.display = 'none';
                document.getElementById(`btn-send-${userId}`).style.display = 'inline-block';
                const status = document.getElementById(`status-${userId}`);
                status.innerText = '미발송';
                status.className = 'status-badge status-n';
            } else { alert(data.message); }
        });
}
