
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

////////////////////////////////////////////////////////////////////////////////////////////////////
// 
// イベント：addField関数への仲介
// 詳細：input画面やedit_project画面において、どの＋ボタンがクリックされているのか確認する
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
document.getElementById('add-os').addEventListener('click', function(e) {
    e.preventDefault();
    addField('os');
});

document.getElementById('add-language').addEventListener('click', function(e) {
    e.preventDefault();
    addField('language');
});

document.getElementById('add-framework').addEventListener('click', function(e) {
    e.preventDefault();
    addField('framework');
});

document.getElementById('add-database').addEventListener('click', function(e) {
    e.preventDefault();
    addField('database');
});

document.getElementById('add-containertech').addEventListener('click', function(e) {
    e.preventDefault();
    addField('containertech');
});

document.getElementById('add-cicd').addEventListener('click', function(e) {
    e.preventDefault();
    addField('cicd');
});

document.getElementById('add-logging').addEventListener('click', function(e) {
    e.preventDefault();
    addField('logging');
});

document.getElementById('add-tools').addEventListener('click', function(e) {
    e.preventDefault();
    addField('tools');
});


////////////////////////////////////////////////////////////////////////////////////////////////////
// 
// イベント：リンク無効化メッセージ
// 詳細：リンク無効化メッセージを表示し、フォームの送信も防ぐ
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
// リンク無効化時の処理
document.getElementById('invalidate-link-form').addEventListener('submit', function(event) {
    if (!confirm('本当にリンクを無効にしますか？')) {
        event.preventDefault();  // ユーザーがキャンセルした場合、フォームの送信を防ぐ
    }
});



