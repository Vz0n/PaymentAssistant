const id = document.getElementById("payment_id").value;
const csrf_token = document.getElementsByName("csrf_token")[0].value;

var action = async (action) => {
    let resp = await fetch(`/admin/payments/${action}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf_token
        },
        body: `payment_id=${id}`
    });
    
    let text = await resp.text()

    if(resp.status != 303){
        document.getElementsByClassName("message")[0].textContent = text
        return;
    }
     
    window.location = text;
}

// Add two listeners for the cancel and accept button.
document.getElementById("accept").addEventListener("click", (ev) => action("accept"));
document.getElementById("reject").addEventListener("click", (ev) => action("reject"));