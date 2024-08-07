
////////////////////////////////////////////////////////////////////////////////////////////////////
// 
// 関数名：addField関数
// 詳細：input画面やedit_project画面において、＋ボタンがクリックされたときに入力項目を追加する
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
// function addField(field) {
//     var fieldsContainer = document.getElementById(field + '-fields');
//     var newFieldCount = fieldsContainer.children.length + 1; // Number to ensure unique ID

//     if (fieldsContainer.style.display === 'none') {
//         fieldsContainer.style.display = 'block';
//     }

//     var newFieldHtml = `
//         <div class="input-group">
//             <input class="input input-name" type="text" name="${field}_${newFieldCount - 1}" placeholder="技術名">
//             <input class="input input-duration" type="number" name="${field}_${newFieldCount - 1}_num" placeholder="期間">
//             <span>ヶ月</span>
//         </div>
//     `;
//     fieldsContainer.insertAdjacentHTML('beforeend', newFieldHtml);
// }

// function removeField(field) {
//     var fieldsContainer = document.getElementById(field + '-fields');
//     if (fieldsContainer.children.length > 0) {
//         fieldsContainer.removeChild(fieldsContainer.lastChild);
//         if (fieldsContainer.children.length === 0) {
//             fieldsContainer.style.display = 'none';
//         }
//     }
// }


