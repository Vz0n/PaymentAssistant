const id = document.getElementById("payment_id").value;
const csrf_token = document.getElementById("csrf_token").value;

async function action(action) {
    let reason = document.getElementById("reject-reason").value;

    let resp = await fetch(`/admin/payments/${action}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf_token
        },
        body: `payment_id=${id}&reason=${reason}`
    });
    
    let text = await resp.text();

    if(resp.status == 204){
        window.location = "/admin/payments";
        return;
    }

    document.getElementById("message").textContent = text;
}

// Add two listeners for the cancel and accept button.
document.getElementById("accept").addEventListener("click", (ev) => action("accept"));
document.getElementById("reject").addEventListener("click", (ev) => action("reject"));