"use strict";

const $ = document.querySelector.bind(document);
const $$ = document.querySelectorAll.bind(document);
const quickPostForm = document.getElementById('quickPostForm');
const postsLinks = $$('.post .postHeader .postLink, .opPost > .opPostHeader .postLink');
const quickPostFormTextArea = document.querySelector('#quickPostForm > textarea');
const postForm = document.getElementById('postForm');
const onClick = twoTapsOnTouchDevices();

for (let f of document.getElementsByTagName('form')) f.addEventListener('submit', submitForm);

$$('.clear-file-btn').forEach((btn) => btn.addEventListener('click', function (ev) {
    ev.target.previousElementSibling.value = '';
    btn.style.visibility = 'hidden';
}));

$$('#id_file').forEach(function (file) {
    if (file.files.length > 0) file.nextElementSibling.style.visibility = 'visible';
    file.addEventListener('change', (ev) => ev.target.nextElementSibling.style.visibility = 'visible');
});
captchaRefresh();

function vote(button, vote) {
    const postElmnt = button.closest('article');
    const url = '/postvote/?' + new URLSearchParams({
        'post': postElmnt.dataset.id,
        'vote': vote,
    });
    fetch(url)
        .then((r) => r.json())
        .then(r => {
            postElmnt.querySelector('#vote').innerText = r.vote;
        });
}

function markUpBtn(btn, tagStart, tagEnd) {
    let elmnt = btn.form.querySelector('textarea');
    let selStart = elmnt.selectionStart;
    let selEnd = elmnt.selectionEnd;
    let textBefore = elmnt.value.substring(0, selStart);
    let selected = elmnt.value.substring(selStart, selEnd);
    let textAfter = elmnt.value.substring(selEnd, elmnt.value.length);
    elmnt.value = textBefore + tagStart + selected + tagEnd + textAfter;
    elmnt.setSelectionRange(selStart + tagStart.length, selEnd + tagStart.length);
    elmnt.focus();
}

if ($('.threadList,.threadPage')) { // at least one class ("OR")
    showQuickPostForm();
    dragPostForm(document.getElementById("quickPostHeader"));
    ApplyJsOnFetchedElements();
    addRepliesToPost();
    altEnterFormSubmit();
    insertEmbedVideoButton();
    $$('.image').forEach((image) => image.addEventListener('click', expandImage));
    $$('.video-thumb').forEach((video) => video.addEventListener('click', expandVideo));
    $('.js-fetch-new-posts')?.addEventListener('click', fetchNewPosts);
    $$('.quote, .reply').forEach((elmnt) => elmnt.addEventListener('click', onClick));
    document.addEventListener('mouseover', function (ev) {
        if (ev.target.classList.contains('quote') || ev.target.classList.contains('reply')) {
            if (!ev.target.hasOwnProperty('_tippy')) {
                const loadAndShow = true;
                addTooltip(ev.target, loadAndShow);
            }
        }
    });
    if ($('.threadPage')) {
        let textAreas = $$('form textarea');
        textAreas[0].addEventListener('input', () => textAreas[1].value = textAreas[0].value)
        textAreas[1].addEventListener('input', () => textAreas[0].value = textAreas[1].value)
    }
    if ($('.container').classList.contains('threadList')) truncateLongPosts();
    if ($$('.page-link').length === 1) $('.page-link').hidden = true;
}

async function submitForm(ev) {
    ev.preventDefault();
    let form = new FormData(ev.target);
    let validated = await validateCaptcha(form);
    if (validated['status'] === 1) {
        await makePost(form, ev.target);
    } else {
        ev.target.querySelector('.errorlist').innerText = '';
        ev.target.querySelector('.errorlist').innerText = validated['err'];
        // Object.values(validated['err']).forEach((v) => ev.target.querySelector('.errorlist').innerText += `${v}\n`);
        ev.target.querySelector('.errorlist').hidden = false;
    }
}

async function validateCaptcha(form) {
    let hash = form.get('captcha_0');
    let captcha = form.get('captcha_1');
    const url = `${window.location.origin}/captcha_val/?` + new URLSearchParams({
        'hash': hash,
        'captcha': captcha,
    });
    const r = await fetch(url);
    return r.json();
}

async function makePost(form, formElmnt) {
    let r = await fetch(window.location.origin + '/posting/', {
        body: form,
        method: "POST",
        headers: {'X-Requested-With': 'XMLHttpRequest'},
    });
    if (r.status === 200) {
        let data = await r.json();
        if ('postok' in data) {
            if ($('.threadPage')) {
                fetchNewPosts();
                formElmnt.reset();
                if (formElmnt.id === 'quickPostForm') formElmnt.hidden = true;
                formElmnt.querySelector('.errorlist').hidden = true;
                formElmnt.querySelector('.captcha').click();
                formElmnt.querySelector('.clear-file-btn').style.visibility = 'hidden';
            }
            if ($('.threadList')) {
                location.href = location.pathname + 'thread/' + data['thread_id'] + '/#bottom';
            }
        } else {
            Object.values(data.errors).forEach((v) => formElmnt.querySelector('.errorlist').innerText += `${v}\n`);
            formElmnt.querySelector('.errorlist').hidden = false;
        }
    }
}

function truncateLongPosts() {
    for (let t of document.getElementsByClassName('text')) {
        if (t.textContent.length > 1500) {
            const span = document.createElement('span');
            span.className = 'func-btn';
            span.innerText = ' ……[⤡]';
            const textAfter = t.innerHTML.substring(1100);
            t.innerHTML = t.innerHTML.substring(0, 1100);
            t.append(span);
            span.addEventListener('click', () => {
                span.remove();
                t.innerHTML += textAfter;
            });
        }
    }
}

function expandVideo(click) {
    click.preventDefault();
    let spanBtn = document.createElement('span');
    spanBtn.innerText = '[❌]';
    spanBtn.className = 'video-close-btn';
    click.target.closest('.video-div').previousElementSibling.after(spanBtn);
    click.target.hidden = true;
    let expandedVideo = document.createElement('video');
    click.target.closest('.video-div').className = 'video-div-expanded';
    expandedVideo.className = 'video-expanded';
    expandedVideo.src = click.target.parentElement.href;
    expandedVideo.setAttribute("controls", "controls");
    expandedVideo.setAttribute("loop", "loop");
    expandedVideo.setAttribute("autoplay", "autoplay");
    click.target.parentNode.appendChild(expandedVideo);
    spanBtn.addEventListener('click', function () {
        expandedVideo.previousElementSibling.hidden = false;
        expandedVideo.closest('.video-div-expanded').className = 'video-div';
        expandedVideo.remove();
        spanBtn.remove();
    });
}

function twoTapsOnTouchDevices() {
    let clicks = 0;
    let target;

    return function (ev) {
        if (ev.target !== target) {
            clicks--;
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
    $$('.text').forEach((el) => {
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
    a.innerText = ' [⤡] ';
    a.href = 'https://' + url;
    a.className = 'func-btn'
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

function captchaRefresh() {
    const url = `${window.location.origin}/captcha/refresh/`;
    $$('img.captcha').forEach((captcha) => captcha.addEventListener('click', function (el) {
            const form = el.target.closest('form');
            form['captcha_1'].value = '';
            form['captcha_1'].focus();
            fetch(url, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                }
            })
                .then((r) => r.json())
                .then(json => {
                    form['captcha_0'].value = json.key;
                    form.querySelector(".captcha").src = json['image_url'];
                    form.querySelector('.errorlist').innerText = '';
                })
                .catch(console.error);
        }
    ));
}

function addTooltip(quoteElmnt, loadAndShow = false) {
    let tooltip;
    try {
        tooltip = $(`[data-id='${quoteElmnt.dataset.quote}']`).outerHTML;
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
            interactive: true,
            interactiveDebounce: 55,
            content: template.content.firstChild,
            placement: 'top-end', //top right-end
            maxWidth: 800,
            arrow: false,
            animation: false,
            offset: [40, 1],
            appendTo: quoteElmnt.closest('.container'), // appendTo: quoteElmnt.parentNode,
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
    $$('.threadPage .quote').forEach((quote) => {
        if (quote.dataset.quote !== previousQuote || quote.closest('article').dataset.id !== previousPostId) {
            previousQuote = quote.dataset.quote;
            previousPostId = quote.closest('article').dataset.id;
            constructReplyElmnt(quote);
        }
    });
}

function constructReplyElmnt(quote) {
    const postId = quote.closest('article').dataset.id;
    const text = '>>' + quote.closest('article').dataset.id + ' ';
    const template = document.createElement('template');
    template.innerHTML = `<span><a class='reply' data-quote=${postId} href='#id${postId}'>${text}</a></span>`;
    const quotedPost = $(`[data-id="${quote.dataset.quote}"]`);
    if (quotedPost !== null) {
        quotedPost.querySelector('.replies').appendChild(template.content.firstChild);
    }
}

function fetchNewPosts() {
    const lastLoadedPost = $$('article')[$$('article').length - 1];
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
                    // addTooltip(quote);
                    // addTooltip($(`.reply[data-quote="${quote.closest('.post').dataset.id}"]`));
                });
            }
        });
    }

    const observer = new MutationObserver(callback);
    $$('section').forEach((elmnt) => {
        observer.observe(elmnt, {childList: true});
    });
}

function expandImage(click) {
    click.preventDefault();
    click.target.hidden = true;  // click.target == imgClicked.target
    let expandedImg = document.createElement('img');
    click.target.closest('.imagediv').className = 'imagediv-expanded';
    expandedImg.src = click.target.parentElement.href;
    expandedImg.style.width = '100%';
    click.target.parentNode.appendChild(expandedImg);
    expandedImg.addEventListener('click', function (e) {
        e.preventDefault();
        expandedImg.previousElementSibling.hidden = false;
        expandedImg.closest('.imagediv-expanded').className = 'imagediv';
        expandedImg.remove();
    });
}

function showQuickPostForm() {
    quickPostForm.elements['id_file'].required = false;
    postsLinks.forEach((link) => link.addEventListener('click', setTextValue));
    document.getElementById('closebutton').addEventListener('click', () => {
        quickPostForm.hidden = true;
        quickPostFormTextArea.value = '';
    });
}

function setTextValue(ev) {
    ev.preventDefault();
    let textArea;
    if ($('details').open && $('.threadPage')) {
        textArea = postForm.elements['text'];
    } else {
        textArea = quickPostForm.elements['text'];
        quickPostForm.hidden = false;
    }
    textArea.setRangeText(`>>` + ev.target.closest('article').dataset.id + '\n');
    textArea.selectionStart = textArea.selectionEnd = textArea.value.length;
    try {
        if (window.getSelection().anchorNode.parentElement.closest('article').id === ev.target.closest('article').id) {
            const selectedText = window.getSelection().toString().trimEnd();
            if (selectedText.length > 0) {
                textArea.value += '>';
                textArea.value += selectedText.replace(/\n/g, '\n>');
                textArea.value += '\n';
            }
        }
    } catch (e) {
    }
    quickPostForm.elements['id_thread_id'].value = ev.target.closest('section').dataset.threadid;
    $('#quickPostHeader #num').innerText = '№ ' + ev.target.closest('section').dataset.threadid;
    textArea.focus();
    textArea.dispatchEvent(new Event('input'));

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
        let winW = document.body.clientWidth;
        let winH = document.body.clientHeight;
        let maxX = winW - elmnt.parentNode.offsetWidth;
        let maxY = winH - elmnt.parentNode.offsetHeight;

        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        if ((elmnt.parentNode.offsetTop - pos2) <= maxY && (elmnt.parentNode.offsetTop - pos2) >= 0) {
            elmnt.parentNode.style.top = (elmnt.parentNode.offsetTop - pos2) + "px";
        }
        if ((elmnt.parentNode.offsetLeft - pos1) <= maxX && (elmnt.parentNode.offsetLeft - pos1) >= 0) {
            elmnt.parentNode.style.left = (elmnt.parentNode.offsetLeft - pos1) + "px";
        }
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
}

function focusTextArea() {
    $('#postForm > textarea').focus();
}

function altEnterFormSubmit() {
    $$('textarea').forEach((area) => area.addEventListener('keydown', (ev) => {
        if (ev.altKey && ev.code === 'Enter') {  // form.submit() doesn't trigger 'submit' event (????)
            ev.target.parentElement.querySelector('button[type="submit"]').click();
        }
    }));
}
