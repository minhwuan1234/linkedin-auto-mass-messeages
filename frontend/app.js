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

const results =
    document.getElementById("results");


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

    const data = await response.json();

    if (!data.ok) {
        alert(
            data.error || "Could not start job."
        );

        startButton.disabled = false;

        return;
    }

    pollStatus();
}


startButton.addEventListener(
    "click",
    startMessaging
);


async function pollStatus() {
    const response = await fetch(
        "/api/messages/status"
    );

    const state = await response.json();

    renderState(
        state
    );

    if (state.status === "running") {
        setTimeout(
            pollStatus,
            1000
        );

        return;
    }

    startButton.disabled = false;
}


function renderState(state) {
    systemStatus.textContent =
        state.status || "idle";

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
            ? (processed / total) * 100
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

    if (state.status === "running") {
        progressLabel.textContent =
            "Messaging in progress";
    }

    else if (
        state.status === "completed"
    ) {
        progressLabel.textContent =
            "Completed";
    }

    else {
        progressLabel.textContent =
            "No active run";
    }

    renderCurrent(
        state.current
    );

    renderResults(
        state.results || []
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

    currentProfile.innerHTML = `
        <div class="result-name">
            ${
                current.full_name
                || "Opening profile..."
            }
        </div>

        <div class="result-url">
            ${current.url}
        </div>
    `;
}


function renderResults(items) {
    if (!items.length) {
        results.innerHTML = `
            <div class="empty-state">
                No results yet.
            </div>
        `;

        return;
    }

    results.innerHTML =
        items
        .slice()
        .reverse()
        .map(item => {
            const statusClass =
                item.status === "sent"
                    ? "status-sent"
                    : "status-failed";

            return `
                <div class="result-row">

                    <div>
                        <div class="result-name">
                            ${
                                item.full_name
                                || item.url
                            }
                        </div>

                        <div class="result-url">
                            ${item.url}
                        </div>

                        ${
                            item.error
                                ? `
                                    <div class="result-url">
                                        ${item.error}
                                    </div>
                                `
                                : ""
                        }
                    </div>

                    <strong
                        class="${statusClass}"
                    >
                        ${item.status}
                    </strong>

                </div>
            `;
        })
        .join("");
}


updateUrlCount();
