
// 페이지 로드 시 상품명 일괄 자동 입력
document.addEventListener("DOMContentLoaded", function() {
document.querySelectorAll('.prize-cell').forEach(cell => {
    const score = cell.getAttribute('data-score');
    cell.innerText = PrizeManager.getPrizeName(score);
});
});

function toggleEditMode(memoId, isEdit) {
const viewLayer = document.getElementById(`view-layer-${memoId}`);
const editLayer = document.getElementById(`edit-layer-${memoId}`);
const btnEdit = document.getElementById(`btn-edit-${memoId}`);
const btnDel = document.getElementById(`btn-del-${memoId}`);
const btnSave = document.getElementById(`btn-save-${memoId}`);
const btnCancel = document.getElementById(`btn-cancel-${memoId}`);

if (isEdit) {
viewLayer.style.display = "none"; editLayer.style.display = "block";
btnEdit.style.display = "none"; btnDel.style.display = "none";
btnSave.style.display = "inline-block"; btnCancel.style.display = "inline-block";
} else {
viewLayer.style.display = "block"; editLayer.style.display = "none";
btnEdit.style.display = "inline-block"; btnDel.style.display = "inline-block";
btnSave.style.display = "none"; btnCancel.style.display = "none";
}
}

function saveMemo(memoId) {
const textarea = document.getElementById(`textarea-${memoId}`);
const updatedContent = textarea.value.trim();
if(!updatedContent) { alert("내용을 입력해 주세요."); return; }

fetch(`/api/memo/update/${memoId}`, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ content: updatedContent })
})
.then(res => res.json())
.then(data => {
if(data.success) {
document.getElementById(`view-layer-${memoId}`).innerText = updatedContent;
toggleEditMode(memoId, false);
} else { alert(data.message); }
}).catch(() => alert("에러가 발생했습니다."));
}

function deleteMemo(memoId) {
if(!confirm("정말 삭제하시겠습니까?")) return;
fetch(`/api/memo/delete/${memoId}`, { method: 'POST' })
.then(res => res.json())
.then(data => {
if(data.success) { document.getElementById(`memo-box-${memoId}`).remove(); }
else { alert(data.message); }
});
}
