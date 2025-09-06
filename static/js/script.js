/*
  Utilities functions 
*/

const COLOR_ANIMATION = [
    {
        "color": "initial",
    },
    {
        "color": "var(--hover-color)",
        "text-transform": "underline"
    }
]

var is_blurried = false;

async function transitionLabel(reverse, labelname){
    const match = document.querySelector(`label[for=${labelname}]`);

    match.animate(COLOR_ANIMATION, {
        direction: reverse ? "reverse" : "normal",
        fill: "both",
        duration: 100 
    });
}

/* 
  Setup functions

  Those functions are used to animate the page and make some part of it usable.
*/

function setupLinks(){
    var links = document.getElementsByClassName("link-button");

    for(let link of links){ 
        let href = link.getAttribute("data-href");

        link.addEventListener("click", (e) => {
            if(href.startsWith("/")){
                window.location = `${href}`;
            } else {
                window.location = `${window.location.href}${href}`;
            }
        });
    }
}

function blur_page(){
    let element = document.querySelector("div[data-to-blurry]");

    element.style.filter = !is_blurried ? "blur(4px)" : "";
    is_blurried = !is_blurried;
}

function setupLabels(){
    var inputs = document.getElementsByTagName("input");

    for(let input of inputs){
       let labelname = input.getAttribute("name");

       if(labelname == "csrf_token") continue;

       input.addEventListener("focusin", (ev) => transitionLabel(false, labelname));
       input.addEventListener("focusout", (ev) => transitionLabel(true, labelname));
    }
}

// Prepare everything

setupLinks();

let form = document.getElementById("content-form")
let dropdown_menu = document.getElementById("dropdown-menu");

if(form != null) setupLabels();

// Listen to popovers to blur the page
for(node of document.querySelectorAll("button[popovertarget]")){
    node.addEventListener("click", (ev) => blur_page());
}



