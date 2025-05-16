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

async function translateLabel(reverse, labelname){
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
    var links = document.getElementsByClassName("link");

    for(let link of links){ 
        let href = link.getAttribute("data-href");

        link.addEventListener("click", (e) => window.location = `/${href}`);
    }
}

function setupLabels(){
    var inputs = document.getElementsByTagName("input");

    for(let input of inputs){
       let labelname = input.getAttribute("name");

       if(labelname == "csrf_token") continue;

       input.addEventListener("focusin", (ev) => translateLabel(false, labelname));
       input.addEventListener("focusout", (ev) => translateLabel(true, labelname));
    }
}

// Prepare everything

setupLinks();

if(document.getElementById("content-form") != null) setupLabels();


