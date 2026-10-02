"""JavaScript snippets executed inside the Scribd embed page."""

COUNT_PAGES = "return document.querySelectorAll('.outer_page').length;"

# Dismiss and remove cookie / consent / privacy banners.
HIDE_COOKIES = """
const closeButtonSelectors = [
    '[class*="cookie"] [class*="close"]',
    '[class*="cookie"] [class*="dismiss"]',
    '[class*="cookie"] button[aria-label*="close"]',
    '[class*="cookie"] button[aria-label*="Close"]',
    '[class*="consent"] [class*="close"]',
    '[class*="consent"] [class*="dismiss"]',
    '[class*="banner"] [class*="close"]',
    '[class*="banner"] [class*="dismiss"]',
    '[class*="notice"] [class*="close"]',
    '[class*="notice"] [class*="dismiss"]',
    'button[class*="close"]',
    'button[aria-label="Close"]',
    'button[aria-label="close"]',
    'button[aria-label="Dismiss"]',
    '[data-dismiss]',
    '[role="button"][class*="close"]'
];

closeButtonSelectors.forEach((selector) => {
    try {
        document.querySelectorAll(selector).forEach((button) => button.click());
    } catch (error) {}
});

const cookieSelectors = [
    '[class*="cookie"]',
    '[class*="Cookie"]',
    '[class*="consent"]',
    '[class*="Consent"]',
    '[class*="gdpr"]',
    '[class*="GDPR"]',
    '[id*="cookie"]',
    '[id*="Cookie"]',
    '[id*="consent"]',
    '[id*="gdpr"]',
    '[class*="privacy-notice"]',
    '[class*="Privacy"]',
    '[class*="cookie-banner"]',
    '[class*="cookie-notice"]',
    '[class*="cookie-popup"]',
    '[class*="cookie-modal"]',
    '[class*="CookieConsent"]',
    '[class*="notice-banner"]',
    '.cc-window',
    '.cc-banner',
    '#onetrust-consent-sdk',
    '#onetrust-banner-sdk',
    '.evidon-banner',
    '.truste_box_overlay',
    '[class*="osano-cm"]',
    '[id*="osano"]'
];

cookieSelectors.forEach((selector) => {
    try {
        document.querySelectorAll(selector).forEach((element) => element.remove());
    } catch (error) {}
});

document.querySelectorAll('*').forEach((element) => {
    try {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        const text = (element.innerText || '').toLowerCase();
        const fixedAtTop =
            (style.position === 'fixed' || style.position === 'sticky') &&
            rect.top < 100;

        if (
            fixedAtTop &&
            (
                text.includes('cookie') ||
                text.includes('privacy') ||
                text.includes('consent') ||
                text.includes('analytics') ||
                text.includes('advertising') ||
                text.includes('personalization')
            )
        ) {
            element.remove();
        }
    } catch (error) {}
});
"""

# Remove toolbars and un-constrain the scroll container so pages can print.
# Returns {toolbarTop, toolbarBottom, containers}.
PREPARE_FOR_PRINT = """
const removed = { toolbarTop: false, toolbarBottom: false, containers: 0 };

const toolbarTop = document.querySelector('.toolbar_top');
if (toolbarTop) {
    toolbarTop.remove();
    removed.toolbarTop = true;
}

const toolbarBottom = document.querySelector('.toolbar_bottom');
if (toolbarBottom) {
    toolbarBottom.remove();
    removed.toolbarBottom = true;
}

document.querySelectorAll('.document_scroller').forEach((element) => {
    element.setAttribute('data-scribd-print-root', 'true');
    element.style.position = 'static';
    element.style.top = 'auto';
    element.style.bottom = 'auto';
    element.style.left = 'auto';
    element.style.right = 'auto';
    element.style.overflow = 'visible';
    element.style.maxHeight = 'none';
    element.style.height = 'auto';
    element.style.margin = '0';
    element.style.padding = '0';
    removed.containers += 1;
});

return removed;
"""

# Conservative print CSS that hides banners without hiding document content.
INJECT_PRINT_STYLES = """
const existing = document.getElementById('scribd-print-styles');
if (existing) {
    existing.remove();
}

const style = document.createElement('style');
style.id = 'scribd-print-styles';
style.textContent = `
    [class*="cookie"],
    [class*="Cookie"],
    [class*="consent"],
    [class*="Consent"],
    [class*="gdpr"],
    [class*="privacy-notice"],
    [class*="notice-banner"],
    [id*="cookie"],
    [id*="consent"],
    [class*="osano-cm"],
    [id*="osano"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    [data-scribd-print-root="true"],
    .document_scroller {
        position: static !important;
        top: auto !important;
        right: auto !important;
        bottom: auto !important;
        left: auto !important;
        overflow: visible !important;
        height: auto !important;
        max-height: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    @media print {
        html,
        body {
            margin: 0 !important;
            padding: 0 !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        .toolbar_top,
        .toolbar_bottom {
            display: none !important;
        }

        [data-scribd-print-root="true"],
        .document_scroller {
            position: static !important;
            top: auto !important;
            right: auto !important;
            bottom: auto !important;
            left: auto !important;
            overflow: visible !important;
            height: auto !important;
            max-height: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        mjx-container,
        .MathJax,
        .katex,
        math,
        svg {
            visibility: visible !important;
            overflow: visible !important;
        }
    }
`;

document.head.appendChild(style);
"""

# Args: [pageNumbers, timeoutMs]. Async; resolves {supported, failed: [{pageNum, reason}]}.
LOAD_PAGES = """
const pageNumbers = arguments[0];
const timeoutMs = arguments[1];
const done = arguments[arguments.length - 1];
const manager = window.docManager;

if (!manager || !manager.pages) {
    done({supported: false});
    return;
}

const states = pageNumbers.map((pageNum) => ({
    pageNum,
    page: manager.pages[pageNum],
    error: null
}));
const startedAt = Date.now();

for (const state of states) {
    if (!state.page) {
        state.error = 'page object missing';
        continue;
    }

    try {
        if (!state.page.innerPageElem && !state.page.loadHasStarted) {
            state.page.load();
        }
    } catch (error) {
        state.error = String(error);
    }
}

const timer = setInterval(() => {
    let ready = 0;

    for (const state of states) {
        if (state.error) {
            ready += 1;
            continue;
        }

        const page = state.page;
        if (!page.innerPageElem) {
            continue;
        }

        try {
            page.display();
            if (!page._imagesTurnedOn) {
                page.turnOnImages();
            }
        } catch (error) {
            state.error = String(error);
            ready += 1;
            continue;
        }

        const images = Array.from(
            page.innerPageElem.querySelectorAll('img')
        );
        const pending = images.filter((image) => !image.complete);

        if (pending.length === 0) {
            ready += 1;
        }
    }

    if (ready === states.length) {
        clearInterval(timer);
        done({
            supported: true,
            failed: states
                .filter((state) => state.error)
                .map((state) => ({
                    pageNum: state.pageNum,
                    reason: state.error
                }))
        });
        return;
    }

    if (Date.now() - startedAt >= timeoutMs) {
        clearInterval(timer);
        done({
            supported: true,
            failed: states
                .filter((state) => (
                    state.error ||
                    !state.page ||
                    !state.page.innerPageElem ||
                    Array.from(
                        state.page.innerPageElem.querySelectorAll('img')
                    ).some((image) => !image.complete)
                ))
                .map((state) => ({
                    pageNum: state.pageNum,
                    reason: state.error || 'page or image load timed out'
                }))
        });
    }
}, 50);
"""

# Args: [pageNumbers]. Frees the memory held by already-exported pages.
RELEASE_PAGES = """
const manager = window.docManager;
if (!manager || !manager.pages) {
    return;
}

for (const pageNum of arguments[0]) {
    const page = manager.pages[pageNum];
    if (!page) {
        continue;
    }

    try {
        page.remove();
    } catch (error) {
        const container = document.getElementById(`outer_page_${pageNum}`);
        if (container) {
            const inner = container.querySelector('.newpage');
            if (inner) {
                inner.remove();
            }
        }
    }
}
"""

# Args: [pageIndex]. Makes only that page printable, sized to the page itself.
# Returns {width, height} in CSS pixels, or null if the page is missing.
ISOLATE_PAGE = """
const targetIndex = arguments[0];
const pages = Array.from(document.querySelectorAll('.outer_page'));
const target = pages[targetIndex];

if (!target) {
    return null;
}

const oldStyle = document.getElementById('isolated-page-print-style');
if (oldStyle) {
    oldStyle.remove();
}

// Restore every page before measuring.
pages.forEach((page) => {
    [
        'display', 'visibility', 'position', 'top', 'left', 'right', 'bottom',
        'margin', 'break-after', 'page-break-after', 'break-before',
        'page-break-before'
    ].forEach((property) => page.style.removeProperty(property));
    page.removeAttribute('data-export-target');
});

const rect = target.getBoundingClientRect();
const width = Math.ceil(rect.width);
const height = Math.ceil(rect.height);

target.setAttribute('data-export-target', 'true');

const style = document.createElement('style');
style.id = 'isolated-page-print-style';
style.textContent = `
    @page {
        size: ${width}px ${height}px;
        margin: 0;
    }

    @media print {
        html,
        body {
            width: ${width}px !important;
            height: ${height}px !important;
            min-width: ${width}px !important;
            min-height: ${height}px !important;
            max-width: ${width}px !important;
            max-height: ${height}px !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        .outer_page {
            display: none !important;
        }

        .outer_page[data-export-target="true"] {
            display: block !important;
            visibility: visible !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: auto !important;
            bottom: auto !important;
            width: ${width}px !important;
            height: ${height}px !important;
            min-width: 0 !important;
            min-height: 0 !important;
            max-width: none !important;
            max-height: none !important;
            margin: 0 !important;
            padding: 0 !important;
            transform: none !important;
            break-before: auto !important;
            break-after: auto !important;
            break-inside: auto !important;
            page-break-before: auto !important;
            page-break-after: auto !important;
            page-break-inside: auto !important;
            overflow: hidden !important;
        }
    }
`;

document.head.appendChild(style);

return {width, height};
"""
