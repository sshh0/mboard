"use strict";

const quickPostForm = document.getElementById('quickPostForm');
const postsLinks = document.querySelectorAll('.post .postHeader .postLink, .opPost > .opPostHeader .postLink');
const quickPostFormTextArea = document.querySelector('#quickPostForm > textarea');

if (document.querySelector('.container').classList.contains('threadPage')) {
    for (let form of document.getElementsByTagName('form')) form.onsubmit = submitForm;
}

if (!document.querySelector('.container').matches(".captcha-error")) {
    if (document.querySelectorAll('.page-link').length === 1) document.querySelector('.page-link').hidden = true
    showQuickPostForm();
    dragPostForm(document.getElementById("quickPostHeader"));
    ApplyJsOnFetchedElements();
    document.querySelectorAll('.image').forEach((image) => image.addEventListener('click', expandImage));
    document.querySelectorAll('.video-thumb').forEach((video) => video.addEventListener('click', expandVideo));
    addRepliesToPost();
    altEnterFormSubmit();
    document.querySelector('.js-fetch-new-posts')?.addEventListener('click', fetchNewPosts);
    document.querySelectorAll('.quote, .reply').forEach((elmnt) => elmnt.addEventListener('mouseover', function (event) {
        if (!event.target.hasOwnProperty('_tippy')) {
            const loadAndShow = true;
            addTooltip(event.target, loadAndShow);
        }
        elmnt.addEventListener('click', onClick);
    }));
    insertEmbedVideoButton();
}

captcha();
document.querySelectorAll('.clear-file-btn').forEach((btn) => btn.addEventListener('click', function (ev) {
    ev.target.previousElementSibling.value = '';
    btn.style.visibility = 'hidden';
}))
document.querySelectorAll('#id_file').forEach((file) => file.addEventListener('change', function (ev) {
    ev.target.nextElementSibling.style.visibility = 'visible';
}))

function submitForm(ev) {
    ev.preventDefault()
    const formElmnt = ev.target;
    let form = new FormData(formElmnt);
    if (form.get('file').name === "" && form.get('text') === "") {
        formElmnt.querySelector('.errorlist').innerText = 'Заполните форму';
        formElmnt.querySelector('.errorlist').hidden = false;
    } else {
        let hash = formElmnt.querySelector('#id_captcha_0').value;
        let captcha = formElmnt.querySelector('#id_captcha_1').value;
        const url = `${window.location.origin}/captcha_val/?` + new URLSearchParams({
            'hash': hash,
            'captcha': captcha,
        });
        fetch(url)
            .then(resp => resp.json())
            .then(json => {
                if (json.status === 1)
                    return fetch(window.location.origin + '/posting/', {
                        body: form,
                        method: "POST",
                        headers: {'X-Requested-With': 'XMLHttpRequest',},
                    })
                else {
                    throw new Error('Ошибка в капче');
                }
            })
            .then(r => {
                if (r.status === 200) {
                    fetchNewPosts();
                    formElmnt.reset();
                    formElmnt.hidden = true;
                    formElmnt.querySelector('.errorlist').hidden = true;
                    formElmnt.querySelector('.captcha').click();
                    formElmnt.querySelector('.clear-file-btn').style.visibility = 'hidden';
                } else throw new Error('Ошибка постинга');
            })
            .catch((er) => {
                formElmnt.querySelector('.errorlist').innerText = er;
                formElmnt.querySelector('.errorlist').hidden = false;
            })
    }
}

function expandVideo(click) {
    click.preventDefault();
    let spanBtn = document.createElement('span');
    spanBtn.innerText = '[закрыть]';
    spanBtn.className = 'video-close-btn';
    this.closest('.video-div').previousElementSibling.appendChild(spanBtn);
    this.hidden = true;
    let expandedVideo = document.createElement('video');
    this.closest('.video-div').className = 'video-div-expanded';
    expandedVideo.className = 'video-expanded'
    expandedVideo.src = this.parentElement.href;
    expandedVideo.setAttribute("controls", "controls");
    expandedVideo.setAttribute("autoplay", "autoplay");
    this.parentNode.appendChild(expandedVideo);
    spanBtn.addEventListener('click', function () {
        expandedVideo.previousElementSibling.hidden = false;
        expandedVideo.closest('.video-div-expanded').className = 'video-div';
        expandedVideo.remove();
        spanBtn.remove();
    });
}

const onClick = twoTapsOnTouchDevices();

function twoTapsOnTouchDevices() {
    let clicks = 0;
    let target;

    return function (ev) {
        if (ev.target !== target) {
            clicks--
        }
        clicks++;
        if (clicks === 2 || !window.matchMedia("(pointer: coarse)").matches) {
            clicks = 0;
        } else {
            ev.preventDefault();
            ev.target._tippy.setProps({placement: 'top'});
            ev.target._tippy.show();
            target = ev.target;
        }
    };
}

function insertEmbedVideoButton() {
    const regex = /(?:www\.)?(youtu|yewtu)\.?be(?:\.com)?\/?\S*(?:watch|embed)?(?:\S*v=|v\/|\/)([\w\-_]+)&?/;
    document.querySelectorAll('.text').forEach((el) => {
        el.childNodes.forEach((node) => {
            if (node.nodeType === Node.TEXT_NODE) {
                let url = regex.exec(node.nodeValue);
                if (url) {
                    let newSpan = insertLinkIntoString(node.nodeValue, url.index + url[0].length, url[0]);
                    addListeners(newSpan, url[0]);
                    el.replaceChild(newSpan, node);
                }
            }
        });
    });
}

function addListeners(span, url) {
    let a = span.querySelector('a');
    let timeout;
    a.addEventListener('click', function (ev) {
        ev.preventDefault();
        !span.querySelector('iframe') ? embedVideo(span, url) : span.querySelector('div').remove();
    });
    if (!window.matchMedia("(pointer: coarse)").matches) {
        a.addEventListener('mouseenter', function (ev) {
            timeout = setTimeout(function () {
                loadVideoPreview(ev, url, a);
            }, 1000);
        });
        a.addEventListener('mouseleave', function () {
            clearTimeout(timeout);
        });
    }
}

function loadVideoPreview(ev, url, a) {
    if (url.includes('youtu') && !ev.target.hasOwnProperty('_tippy')) {
        fetch('https://www.youtube.com/oembed?url=' + url)
            .then(response => {
                if (!response.ok) {
                    let imgNoVideo = document.createElement('img');
                    imgNoVideo.src = 'https://i.ytimg.com/mqdefault.jpg';
                    tippy(ev.target, {
                        content: imgNoVideo,
                        showOnCreate: true,
                    });
                    return Promise.reject('fetchErr');
                } else return response.json();
            })
            .then(data => {
                let img = document.createElement('img');
                img.src = data['thumbnail_url'];
                img.width = 320;
                img.height = 180;
                tippy(a, {
                    content: img,
                    showOnCreate: true
                });
            });
    }
}


function insertLinkIntoString(text, pos, url) {
    let beginning = document.createTextNode(text.slice(0, pos));
    let end = document.createTextNode(text.slice(pos - text.length));
    let span = document.createElement('span');
    let a = document.createElement('a');
    a.innerText = ' [раскрыть] ';
    a.href = 'https://' + url;
    span.appendChild(beginning);
    span.appendChild(a);
    if (text.length !== beginning.length) {
        span.appendChild(end);
    }
    return span;
}

function embedVideo(span, url) {
    url = url.replace('/watch?v=', '/embed/');
    let embeddiv = document.createElement('div');
    let iframe = document.createElement('iframe');
    iframe.src = 'https://' + url;
    iframe.allowFullscreen = true;
    span.appendChild(embeddiv);
    embeddiv.appendChild(iframe);
}

function captcha() {
    const url = `${window.location.origin}/captcha/refresh/`;
    document.querySelectorAll('img.captcha').forEach((captcha) => captcha.addEventListener('click', function (el) {
            const form = el.target.closest('form');
            form.querySelector('#id_captcha_1').value = '';
            form.querySelector('#id_captcha_1').focus();
            fetch(url, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                }
            })
                .then((r) => r.json())
                .then(json => {
                    form.querySelector("input[name='captcha_0']").value = json.key;
                    form.querySelector(".captcha").src = json['image_url'];
                })
                .catch(console.error);
        }
    ));
}

function addTooltip(quoteElmnt, loadAndShow=false) {
    let tooltip;
    try {
        tooltip = document.querySelector(`[data-id='${quoteElmnt.dataset.quote}']`).outerHTML;
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
            placement: 'top', //right-end
            maxWidth: 800,
            animation: false,
            appendTo: quoteElmnt.parentNode,
        });
        if (loadAndShow === true) t.show();
    }
}

function fetchTippy(quoteElmnt) {
    let fetchURL = quoteElmnt.pathname + quoteElmnt.dataset.quote + '.json';
    return fetch(fetchURL, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            'Content-Type': 'application/json',
        }
    })
        .then((response) => response.json())
        .then((responseData) => {
            return responseData;
        });
}

function addRepliesToPost() {
    let previousQuote;
    let previousPostId;
    document.querySelectorAll('.threadPage .quote').forEach((quote) => {
        if (quote.dataset.quote !== previousQuote || quote.closest('article').dataset.id !== previousPostId) {
            previousQuote = quote.dataset.quote;
            previousPostId = quote.closest('article').dataset.id;
            constructReplyElmnt(quote)
        }
    });
}

function constructReplyElmnt(quote) {
    const postId = quote.closest('article').dataset.id;
    const text = '>>' + quote.closest('article').dataset.id + ' ';
    const template = document.createElement('template');
    template.innerHTML = `<span><a class='reply' data-quote=${postId} href='#id${postId}'>${text}</a></span>`;
    const quotedPost = document.querySelector(`[data-id="${quote.dataset.quote}"]`);
    if (quotedPost !== null) {
        quotedPost.querySelector('.replies').appendChild(template.content.firstChild);
    }
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
            if (response.status === 200) {
                response.json().then(newPosts => insert(newPosts));
            }
            if (response.status === 304) {
                fetchStatus.hidden = false;
                setTimeout(function () {
                    fetchStatus.hidden = true;
                }, 10000); // 10 sec
            }
        });

    function getLastPostDate() {
        const timestamp = lastLoadedPost.querySelector('.date').dataset.unixtime;
        const lastPostDate = new Date(timestamp * 1000);  //milliseconds to seconds
        lastPostDate.setSeconds(lastPostDate.getSeconds() + 1);
        return lastPostDate.toUTCString();

    }
}

function insert(newPosts) {
    const elmntslist = document.getElementsByTagName('article');
    elmntslist[elmntslist.length - 1].insertAdjacentHTML("afterend", newPosts);
}

function ApplyJsOnFetchedElements() {
    function callback(mutationList) {
        mutationList[0].addedNodes.forEach((node) => {
            if (node.className === 'post') {
                node.querySelector('.image')?.addEventListener('click', expandImage);
                node.querySelector('.video-thumb')?.addEventListener('click', expandVideo);
                node.querySelector('.postLink')?.addEventListener('click', setTextValue);
                node.querySelectorAll('.quote')?.forEach((quote) => {
                    constructReplyElmnt(quote);
                    addTooltip(quote);
                    addTooltip(document.querySelector(`[data-id='${quote.dataset.quote}'] .reply`));
                });
            }
        });
    }

    const observer = new MutationObserver(callback);
    document.querySelectorAll('section').forEach((elmnt) => {
        observer.observe(elmnt, {childList: true});
    });
}


function expandImage(click) {
    click.preventDefault();
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
    quickPostForm.elements['id_file'].required = false;
    for (let i = 0; i < postsLinks.length; i++) {
        postsLinks[i].addEventListener('click', setTextValue);
    }
    document.getElementById('closebutton').addEventListener('click', () => {
        quickPostForm.hidden = true;
        quickPostFormTextArea.value = '';
    });
}

function setTextValue(e) {
    e.preventDefault();
    quickPostForm.hidden = false;
    if (!quickPostForm.hidden) {
        {
            quickPostFormTextArea.setRangeText(`>>` + this.closest('article').dataset.id + '\n');
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
            quickPostForm.elements['id_thread_id'].value = this.closest('section').dataset.threadid;
            quickPostFormTextArea.focus();
        }
    }
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
            window.document.activeElement.parentElement.submit();
        }
    }));
}