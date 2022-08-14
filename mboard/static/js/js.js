"use strict";

if (!document.querySelector('.container').matches(".main, .captcha-error")) {
    showQuickPostForm();
    dragPostForm(document.getElementById("quickPostHeader"));
    ApplyJsOnFetchedElements();
    document.querySelectorAll('.image').forEach((image) => image.addEventListener('click', expandImage));
    addRepliesToPost();
    altEnterFormSubmit();
    document.querySelector('.js-fetch-new-posts')?.addEventListener('click', fetchNewPosts);
    document.querySelectorAll('.quote, .reply').forEach((elmnt) => elmnt.addEventListener('mouseover', function (event) {
        if (!event.target.hasOwnProperty('_tippy')) {
            const loadAndShow = true;
            addTooltip(event.target, loadAndShow)
        }
    }));
}
if (!document.querySelector('.container').matches(".main")) captcha();


function captcha() {
    const url = `${window.location.origin}/captcha/refresh/`;
    document.querySelectorAll('img.captcha').forEach((captcha) => captcha.addEventListener('click', function (el) {
            const form = el.target.closest('form');
            fetch(url, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                }
            })
                .then((res) => res.json())
                .then(json => {
                    form.querySelector("input[name='captcha_0']").value = json.key;
                    form.querySelector(".captcha").src = json.image_url;
                })
                .catch(console.error)
        }
    ))
}


function addTooltip(quoteElmnt, loadAndShow = false) {
    let tooltip;
    try {
        tooltip = document.querySelector(`[data-id='${quoteElmnt.dataset['quote']}']`).outerHTML;
        fillTooltip(quoteElmnt, tooltip, loadAndShow);
    } catch (e) { //tooltip content in another thread, get its content via fetch
        fetchTippy(quoteElmnt).then(tooltip => fillTooltip(quoteElmnt, tooltip, loadAndShow));
    }

    function fillTooltip(quoteElmnt, tooltip, loadAndShow) {
        let template = document.createElement('template');
        template.innerHTML = tooltip.trim();
        template.content.firstChild.className = 'postQuote';
        let t = tippy(quoteElmnt, {
            // showOnCreate: true,
            // interactive: true,
            content: template.content.firstChild,
            placement: 'right-end', //top
            maxWidth: 800,
            animation: false,
            appendTo: quoteElmnt.parentNode,
            touch: 'hold',
            // duration: [0, 900],
        })
        if (loadAndShow === true) t.show()
    }
}

function fetchTippy(quoteElmnt) {
    let fetchURL = quoteElmnt.pathname + quoteElmnt.dataset['quote'] + '.json';
    return fetch(fetchURL, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            'Content-Type': 'application/json',
        }
    })
        .then((response) => response.json())
        .then((responseData) => {
            return responseData
        })
}

// function showQuotesOnHover() { //hz cho eto
//     const quotes = document.querySelectorAll('.text');
//     quotes.forEach((quote) => quote.addEventListener('mouseover', function (event) {
//             if (event.target.className === 'quote') {
//                 if (!event.target.hasOwnProperty('_tippy')) {
//                     const quoteElmnt = event.target;
//                     const loadAndShow = true;
//                     fetchTippy(quoteElmnt, loadAndShow)
//                 }
//             }
//         }
//     ))
// }

function addRepliesToPost() {
    let previousQuote;
    let previousPostId;
    document.querySelectorAll('.threadPage .quote').forEach((quote) => {
        if (quote.dataset['quote'] !== previousQuote || quote.closest('article').dataset['id'] !== previousPostId) {
            previousQuote = quote.dataset['quote'];
            previousPostId = quote.closest('article').dataset['id'];
            const postId = quote.closest('article').dataset['id'];
            const text = '>>' + quote.closest('article').dataset['id'] + ' ';
            const template = document.createElement('template');
            template.innerHTML = `<span><a class='reply' data-quote=${postId} href='#id${postId}'>${text}</a></span>`
            const quotedPost = document.querySelector(`[data-id="${quote.dataset['quote']}"]`);
            if (quotedPost != null) {
                quotedPost.querySelector('.replies').appendChild(template.content.firstChild);
            }
        }
    })
}

function fetchNewPosts() {
    const lastLoadedPost = document.querySelectorAll('article')[document.querySelectorAll('article').length - 1];
    let pathname = window.location.pathname;
    pathname = pathname.endsWith('/') ? pathname.slice(0, -1) : pathname;
    const urlparams = pathname + '.json';

    fetch('' + urlparams, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "If-Modified-Since": getLastPostDate(),
        },
    })
        .then(response => {
            const fetchStatus = document.getElementById('fetchStatus');
            if (response.status === 200) response.json().then(newPosts => insert(newPosts))
            if (response.status === 304) {
                fetchStatus.hidden = false;
                setTimeout(function () {
                    fetchStatus.hidden = true
                }, 10000) // 10 sec
            }
        })

    function insert(newPosts) {
        const elmntlist = document.getElementsByTagName('article');
        elmntlist[elmntlist.length - 1].insertAdjacentHTML("afterend", newPosts);
    }

    function getLastPostDate() {
        const dateArray = lastLoadedPost.querySelector('.date').innerText.split(/[/| :]/g);
        [dateArray[0], dateArray[2]] = [dateArray[2], dateArray[0]]; // 10/07/2022 20:30 => 2022/10/07 20:30
        dateArray[1] -= 1;  // months start from 0
        let dateObject = new Date(...dateArray);
        dateObject.setSeconds(dateObject.getSeconds() + 1); // +1 sec from the last post
        return dateObject.toUTCString()  // http date format
    }
}

function ApplyJsOnFetchedElements() {
    function callback(mutationList) {
        mutationList[0].addedNodes.forEach((node) => {
            if (node.className === 'post') {
                node.querySelector('.image')?.addEventListener('click', expandImage);
                node.querySelectorAll('.quote')?.forEach((quote) => {
                    addTooltip(quote)
                })
            }
        })
    }

    const observer = new MutationObserver(callback)
    document.querySelectorAll('section').forEach((elmnt) => {
        observer.observe(elmnt, {childList: true});
    })
}


function expandImage(imgClicked) {
    imgClicked.preventDefault();
    this.hidden = true;  // this == imgClicked.target
    let expandedImg = document.createElement('img');
    this.closest('.imagediv').className = 'imagediv-expanded';
    expandedImg.src = this.parentElement.href;
    expandedImg.style.width = '100%';
    this.parentNode.appendChild(expandedImg);
    expandedImg.addEventListener('click', function (e) {
        e.preventDefault();
        expandedImg.previousElementSibling.hidden = false;
        expandedImg.closest('.imagediv-expanded').className = 'imagediv';
        expandedImg.remove();
    });
}

function showQuickPostForm() {
    const quickPostForm = document.getElementById('quickPostForm');
    const postsLinks = document.querySelectorAll('.post .postHeader .postLink, .opPost > .opPostHeader .postLink');
    const quickPostFormTextArea = document.querySelector('#quickPostForm > textarea');
    // const postForm = document.querySelector('#postForm');
    quickPostForm.elements['id_image'].required = false;
    for (let i = 0; i < postsLinks.length; i++) {
        postsLinks[i].addEventListener('click', setTextValue
        );
    }

    function setTextValue(e) {
        e.preventDefault();
        quickPostForm.hidden = false;
        if (!quickPostForm.hidden) {
            {
                quickPostFormTextArea.setRangeText(`>>` + this.closest('article').dataset['id'] + '\n');
                quickPostFormTextArea.selectionStart = quickPostFormTextArea.selectionEnd = quickPostFormTextArea.value.length;
                try {
                    if (window.getSelection().anchorNode.parentElement.closest('article').id === this.closest('article').id) {
                        const selectedText = window.getSelection().toString().trimEnd();
                        quickPostFormTextArea.value += '>';
                        quickPostFormTextArea.value += selectedText.replace(/\n/g, '\n>');
                        quickPostFormTextArea.value += '\n';
                    }
                } catch (e) {
                }
                quickPostForm.elements['id_threadnum'].value = this.closest('section').dataset['threadid'];
                // if (!postForm.hidden) {
                //     postForm.value = this.closest('section').dataset['threadid'];
                // }
                quickPostFormTextArea.focus();
            }
        }
    }

    document.getElementById('closebutton').addEventListener('click', () => {
        quickPostForm.hidden = true;
        quickPostFormTextArea.value = '';
    });
}

function dragPostForm(elmnt) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    elmnt.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        elmnt.parentNode.style.top = (elmnt.parentNode.offsetTop - pos2) + "px";
        elmnt.parentNode.style.left = (elmnt.parentNode.offsetLeft - pos1) + "px";
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
}

function focusTextArea() {
    document.querySelector('#postForm > textarea').focus();
}

function altEnterFormSubmit() {
    document.querySelectorAll('textarea').forEach((area) => area.addEventListener('keydown', (keyboardEv) => {
        if (keyboardEv.altKey && keyboardEv.code === 'Enter') {
            window.document.activeElement.parentElement.submit()
        }
    }))
}