const urlsInput =
    document.getElementById("urls");

const templateInput =
    document.getElementById("template");

const startButton =
    document.getElementById("start-button");

const urlCount =
    document.getElementById("url-count");

const systemStatus =
    document.getElementById("system-status");

const progressLabel =
    document.getElementById("progress-label");

const progressNumber =
    document.getElementById("progress-number");

const progressBar =
    document.getElementById("progress-bar");

const sentCount =
    document.getElementById("sent-count");

const failedCount =
    document.getElementById("failed-count");

const remainingCount =
    document.getElementById("remaining-count");

const currentProfile =
    document.getElementById("current-profile");

const contactsContainer =
    document.getElementById("contacts");


const ACTIVE_STATUSES = [
    "pending",
    "processing",
    "running",
];


function getUrls() {
    return urlsInput.value
        .split("\n")
        .map(url => url.trim())
        .filter(Boolean);
}


function updateUrlCount() {
    const urls = getUrls();

    urlCount.textContent =
        `${urls.length} profiles`;
}


urlsInput.addEventListener(
    "input",
    updateUrlCount
);


async function startMessaging() {
    const urls = getUrls();

    const template =
        templateInput.value.trim();

    if (!urls.length) {
        alert(
            "Add at least one LinkedIn URL."
        );

        return;
    }

    if (!template) {
        alert(
            "Message template cannot be empty."
        );

        return;
    }

    startButton.disabled = true;

    try {
        const response = await fetch(
            "/api/messages/start",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body: JSON.stringify({
                    urls,
                    template,
                }),
            }
        );

        const data =
            await response.json();

        if (!response.ok) {
            alert(
                data.detail
                || data.error
                || "Could not start job."
            );

            startButton.disabled =
                false;

            return;
        }

        await refreshDashboard();

    }

    catch (error) {
        console.error(
            error
        );

        alert(
            "Could not connect to server."
        );

        startButton.disabled =
            false;
    }
}


startButton.addEventListener(
    "click",
    startMessaging
);


async function fetchStatus() {
    const response = await fetch(
        "/api/messages/status",
        {
            cache: "no-store",
        }
    );

    if (!response.ok) {
        throw new Error(
            "Could not load message status."
        );
    }

    return response.json();
}


async function refreshDashboard() {
    try {
        const state =
            await fetchStatus();

        renderState(
            state
        );

        renderContacts(
            state
        );

        const status =
            state.status || "idle";

        startButton.disabled =
            ACTIVE_STATUSES.includes(
                status
            );

    }

    catch (error) {
        console.error(
            error
        );
    }

    setTimeout(
        refreshDashboard,
        1500
    );
}


function renderState(state) {
    const status =
        state.status || "idle";

    systemStatus.textContent =
        status;

    systemStatus.className =
        `system-status status-${status}`;


    const total =
        state.total || 0;

    const processed =
        state.processed || 0;

    const remaining =
        Math.max(
            total - processed,
            0
        );

    const percent =
        total
            ? (
                processed
                / total
            ) * 100
            : 0;


    progressNumber.textContent =
        `${processed} / ${total}`;

    progressBar.style.width =
        `${percent}%`;

    sentCount.textContent =
        state.sent || 0;

    failedCount.textContent =
        state.failed || 0;

    remainingCount.textContent =
        remaining;


    if (status === "pending") {
        progressLabel.textContent =
            "Waiting for Mac worker";
    }

    else if (
        status === "processing"
        || status === "running"
    ) {
        progressLabel.textContent =
            "Messaging in progress";
    }

    else if (
        status === "completed"
    ) {
        progressLabel.textContent =
            "Completed";
    }

    else if (
        status === "failed"
    ) {
        progressLabel.textContent =
            "Job failed";
    }

    else {
        progressLabel.textContent =
            "No active run";
    }


    renderCurrent(
        state.current
    );
}


function renderCurrent(current) {
    if (!current) {
        currentProfile.classList.add(
            "empty"
        );

        currentProfile.innerHTML =
            "Waiting for a profile.";

        return;
    }


    currentProfile.classList.remove(
        "empty"
    );


    const name =
        current.full_name
        || current.first_name
        || "Opening profile...";

    const step =
        current.step
        || current.status
        || "processing";


    currentProfile.innerHTML = `
        <div class="result-name">
            ${escapeHtml(name)}
        </div>

        <div class="result-url">
            ${escapeHtml(
                current.url || ""
            )}
        </div>

        <div class="contact-step">
            ${escapeHtml(step)}
        </div>
    `;
}


function buildContactsFromJob(state) {
    const urls =
        Array.isArray(state.urls)
            ? state.urls
            : [];

    const results =
        Array.isArray(state.results)
            ? state.results
            : [];

    const current =
        state.current || null;

    const resultMap =
        new Map();


    for (const item of results) {
        if (!item.url) {
            continue;
        }

        resultMap.set(
            item.url,
            item
        );
    }


    return urls.map(
        (url, index) => {

            const result =
                resultMap.get(
                    url
                );


            if (result) {
                return {
                    index:
                        result.index
                        || index + 1,

                    url,

                    full_name:
                        result.full_name
                        || "",

                    first_name:
                        result.first_name
                        || "",

                    status:
                        result.status
                        || "completed",

                    step:
                        result.step
                        || "",

                    error:
                        result.error
                        || "",
                };
            }


            if (
                current
                && current.url === url
            ) {
                return {
                    index:
                        current.index
                        || index + 1,

                    url,

                    full_name:
                        current.full_name
                        || "",

                    first_name:
                        current.first_name
                        || "",

                    status:
                        "processing",

                    step:
                        current.step
                        || "processing",

                    error:
                        current.error
                        || "",
                };
            }


            let waitingStatus =
                "queued";


            if (
                state.status === "pending"
            ) {
                waitingStatus =
                    "waiting";
            }


            return {
                index: index + 1,

                url,

                full_name: "",

                first_name: "",

                status:
                    waitingStatus,

                step: "",

                error: "",
            };
        }
    );
}


function renderContacts(state) {
    const contacts =
        buildContactsFromJob(
            state
        );


    if (!contacts.length) {
        contactsContainer.innerHTML = `
            <div class="empty-state">
                No contacts yet.
            </div>
        `;

        return;
    }


    contactsContainer.innerHTML =
        contacts
        .map(contact => {

            const status =
                contact.status
                || "queued";

            const name =
                contact.full_name
                || contact.first_name
                || `Contact ${contact.index}`;

            const error =
                contact.error || "";

            const step =
                contact.step || "";


            return `
                <div class="result-row">

                    <div class="contact-main">

                        <div class="result-name">
                            ${escapeHtml(name)}
                        </div>

                        <a
                            class="result-url contact-link"
                            href="${escapeHtml(
                                contact.url
                            )}"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            ${escapeHtml(
                                contact.url
                            )}
                        </a>

                        ${
                            step
                                && status === "processing"
                                ? `
                                    <div class="contact-step">
                                        ${escapeHtml(step)}
                                    </div>
                                `
                                : ""
                        }

                        ${
                            error
                                ? `
                                    <div class="contact-error">
                                        ${escapeHtml(error)}
                                    </div>
                                `
                                : ""
                        }

                    </div>

                    <div
                        class="
                            contact-status
                            status-${escapeHtml(status)}
                        "
                    >
                        ${formatStatus(status)}
                    </div>

                </div>
            `;
        })
        .join("");
}


function formatStatus(status) {
    const labels = {
        waiting:
            "Waiting",

        queued:
            "Queued",

        processing:
            "Processing",

        sent:
            "Sent",

        failed:
            "Failed",

        completed:
            "Completed",
    };

    return (
        labels[status]
        || status
    );
}


function escapeHtml(value) {
    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            "\"",
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


updateUrlCount();

refreshDashboard();
