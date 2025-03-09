function setupLinks(){
    var links = document.getElementsByClassName("link");

    for(let link of links){ 
        let href = link.getAttribute("data-href");

        link.addEventListener("click", (e) => window.location = `/${href}`);
    }
}

setupLinks();