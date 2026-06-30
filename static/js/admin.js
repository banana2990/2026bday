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

function sendPrize(personId) {
    // 서버 요청 로직...
    if(!confirm("상품을 발송 처리하시겠습니까?")) return;
    fetch(`/admin/send-product/${personId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if(data.success) {
                // 버튼 교체: 발송 숨기고 취소 보이기
                document.getElementById(`btn-send-${personId}`).style.display = 'none';
                document.getElementById(`btn-cancel-${personId}`).style.display = 'inline-block';
                // 상태 배지 업데이트 (선택 사항)
                document.getElementById(`status-${personId}`).className = 'status-badge status-y';
                document.getElementById(`status-${personId}`).innerText = '발송완료';
            }
        });
}

function cancelPrize(personId) {
    // 서버 요청 로직...
    fetch(`/admin/cancel/${personId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if(data.success) {
                // 버튼 교체: 취소 숨기고 발송 보이기
                document.getElementById(`btn-cancel-${personId}`).style.display = 'none';
                document.getElementById(`btn-send-${personId}`).style.display = 'inline-block';
                // 상태 배지 업데이트
                document.getElementById(`status-${personId}`).className = 'status-badge status-n';
                document.getElementById(`status-${personId}`).innerText = '미발송';
            }
        });
}