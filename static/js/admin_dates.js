document.getElementById("settings-form").addEventListener('submit', async (ev) => {
    ev.preventDefault();
    
    let dates = ""
    let email = document.getElementById("email").value;
    let price = document.getElementById("fee_price").value;
    let csrf_token = document.getElementsByName("csrf_token")[0].value;

    for(let i = 1; i <= 5; i++){
        let date = document.getElementById(`date-${i}`).value;

        i == 5 ? dates = dates.concat(date) : dates = dates.concat(`${date}|`);
    }

    let resp = await fetch("settings/edit", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token
        },
        body: `dates=${dates}&receipt_email=${email}&fee_price=${price}`
    });
    let text = await resp.text();

    document.getElementById("message").innerText = text;
});