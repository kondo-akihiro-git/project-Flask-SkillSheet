
////////////////////////////////////////////////////////////////////////////////////////////////////
// 
// 関数名：addField関数
// 詳細：input画面やedit_project画面において、＋ボタンがクリックされたときに入力項目を追加する
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
function addField(field) {
    var fieldsContainer = document.getElementById(field + '-fields');
    var newFieldCount = fieldsContainer.children.length + 1; // Number to ensure unique ID

    var newFieldHtml = `
        <div>
            <input type="text" name="${field}_${newFieldCount - 1}">
            <input type="number" name="${field}_${newFieldCount - 1}_num">
            <span>ヶ月</span>
        </div>
    `;
    fieldsContainer.innerHTML += newFieldHtml;
};




