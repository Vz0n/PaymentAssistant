document.getElementById("settings-form").addEventListener('submit', async (ev) => {
    ev.preventDefault();
    
    let dates = ""
    let price = document.getElementById("fee_price").value;
    let csrf_token = document.getElementsByName("csrf_token")[0].value;

    for(let i = 1; i <= 5; i++){
        let date = document.getElementById(`date-${i}`).value;

        dates = i == 5 ? dates.concat(date) : dates.concat(`${date}|`);
    }

    let resp = await fetch("settings/edit", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token
        },
        body: `dates=${dates}&fee_price=${price}`
    });
    let text = await resp.text();

    document.getElementById("message").innerText = text;
});