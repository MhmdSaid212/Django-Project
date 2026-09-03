(function () {
    const sidebar = document.getElementById("sidebar");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    if (toggle && sidebar) {
        toggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });
    }

    document.addEventListener("click", function (event) {
        const collapse = event.target.closest("[data-sidebar-collapse]");

        if (!collapse) return;

        document.body.classList.toggle("sidebar-collapsed");

        localStorage.setItem(
            "tourops-sidebar",
            document.body.classList.contains("sidebar-collapsed")
                ? "collapsed"
                : "open"
        );

        console.log(
            "SIDEBAR COLLAPSED:",
            document.body.classList.contains("sidebar-collapsed")
        );
    });

    if (localStorage.getItem("tourops-sidebar") === "collapsed") {
        document.body.classList.add("sidebar-collapsed");
    }

    const quickBtn = document.querySelector("[data-quick-create]");
    const quickMenu = document.querySelector("[data-quick-menu]");


    if (quickBtn && quickMenu) {
        quickBtn.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            console.log("CREATE CLICKED");

            quickMenu.classList.toggle("hidden");
        });

        quickMenu.addEventListener("click", function (event) {
            event.stopPropagation();
        });

        document.addEventListener("click", function () {
            quickMenu.classList.add("hidden");
        });
    }

    document.querySelectorAll("[data-chips]").forEach(function (group) {
        group.addEventListener("click", function (event) {
            const chip = event.target.closest(".chip");
            if (!chip) return;
            group.querySelectorAll(".chip").forEach(function (item) {
                item.classList.remove("is-on");
            });
            chip.classList.add("is-on");
        });
    });

    function money(n) {
        return "$" + Math.round(n).toLocaleString("en-US");
    }

    const amountInput = document.querySelector("[data-pay-amount]");
    if (amountInput) {
        const remainingEl = document.querySelector("[data-pay-remaining]");
        const afterEl = document.querySelector("[data-pay-after]");
        const errEl = document.querySelector("[data-pay-error]");
        const cap = Number(amountInput.getAttribute("data-max") || 0);
        function updatePay() {
            const value = Number(amountInput.value || 0);
            const after = cap - value;
            if (afterEl) afterEl.textContent = money(Math.max(after, 0));
            if (remainingEl) remainingEl.textContent = money(cap);
            if (errEl) {
                const over = value > cap + 0.001;
                errEl.classList.toggle("show", over);
                if (afterEl) afterEl.classList.toggle("warn", over || after < 0);
            }
        }
        amountInput.addEventListener("input", updatePay);
        updatePay();
    }

    const spAmount = document.querySelector("[data-sp-amount]");
    if (spAmount) {
        const cap = Number(spAmount.getAttribute("data-max") || 0);
        const afterEl = document.querySelector("[data-sp-after]");
        const errEl = document.querySelector("[data-sp-error]");
        spAmount.addEventListener("input", function () {
            const value = Number(spAmount.value || 0);
            if (value > cap) {
                spAmount.value = String(cap);
            }
            const used = Number(spAmount.value || 0);
            if (afterEl) afterEl.textContent = money(cap - used);
            if (errEl) errEl.classList.toggle("show", value > cap);
        });
    }

    document.querySelectorAll("[data-open-drawer]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const id = btn.getAttribute("data-open-drawer");
            const drawer = document.getElementById(id);
            const back = document.getElementById(id + "-back");
            if (drawer) drawer.classList.add("open");
            if (back) back.classList.add("open");
        });
    });
    document.querySelectorAll("[data-close-drawer]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            document.querySelectorAll(".drawer, .drawer-back").forEach(function (el) {
                el.classList.remove("open");
            });
        });
    });

    const wizard = document.querySelector("[data-wizard]");
    if (wizard) {
        let step = 1;
        const total = 6;
        const price = 650;
        function show() {
            wizard.querySelectorAll("[data-step]").forEach(function (panel) {
                panel.hidden = Number(panel.getAttribute("data-step")) !== step;
            });
            wizard.querySelectorAll("[data-wz]").forEach(function (item) {
                const n = Number(item.getAttribute("data-wz"));
                const active = n === step;

                item.classList.toggle("bg-blue-50", active);
                item.classList.toggle("text-brand-blue", active);

                item.classList.toggle("bg-white", !active);
                item.classList.toggle("text-gray-400", !active);
            });
        }
        function recalc() {
            const travelers = Number(wizard.querySelector("[data-travelers]")?.value || 4);
            const discount = Number(wizard.querySelector("[data-discount]")?.value || 0);
            const taxRate = 0.11;
            const subtotal = travelers * price;
            const afterDisc = Math.max(subtotal - discount, 0);
            const tax = Math.round(afterDisc * taxRate);
            const totalAmt = afterDisc + tax;
            const set = function (name, val) {
                wizard.querySelectorAll("[data-sum='" + name + "']").forEach(function (el) {
                    el.textContent = money(val);
                });
            };
            set("sub", subtotal);
            set("disc", discount);
            set("tax", tax);
            set("total", totalAmt);
            wizard.querySelectorAll("[data-sum='pax']").forEach(function (el) {
                el.textContent = String(travelers);
            });
        }
        wizard.addEventListener("click", function (event) {
            console.log("WIZARD CLICK:", event.target);
            const next = event.target.closest("[data-next]");
            const prev = event.target.closest("[data-prev]");
            const pick = event.target.closest(".pick");
            console.log("PICK:", pick);

            if (pick) {
                console.log("PICK CLICKED:", pick);
                const group = pick.parentElement;

                group.querySelectorAll(".pick").forEach(function (p) {
                    p.classList.remove("is-on");
                });

                pick.classList.add("is-on");
            }

            if (next) {
                step = Math.min(total, step + 1);
                console.log("CURRENT STEP:", step);
                show();
            }

            if (prev) {
                step = Math.max(1, step - 1);
                show();
            }
        });
        wizard.addEventListener("input", recalc);
        show();
        recalc();
    }

    const capBar = document.querySelector("[data-animate-cap]");
    if (capBar) {
        const fill = capBar.querySelector("i");
        const label = document.querySelector("[data-cap-label]");
        requestAnimationFrame(function () {
            fill.style.width = capBar.getAttribute("data-to") + "%";
        });
        if (label && capBar.getAttribute("data-demo") === "1") {
            setTimeout(function () {
                label.textContent = "20 / 25 seats";
                fill.style.width = "80%";
            }, 900);
        }
    }

    const toast = document.getElementById("app-toast");
    document.querySelectorAll("[data-toast]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            if (!toast) return;
            toast.textContent = btn.getAttribute("data-toast");
            toast.classList.add("show");
            setTimeout(function () {
                toast.classList.remove("show");
            }, 3200);
        });
    });

    

    document.querySelectorAll("[data-settings-tab]").forEach(function (tab) {
        tab.addEventListener("click", function (event) {
            event.preventDefault();
            const name = tab.getAttribute("data-settings-tab");
            document.querySelectorAll("[data-settings-tab]").forEach(function (t) {
                t.classList.toggle("is-on", t === tab);
            });
            document.querySelectorAll("[data-settings-panel]").forEach(function (panel) {
                panel.hidden = panel.getAttribute("data-settings-panel") !== name;
            });
        });
    });
    $(document).ready(function () {
        $("#nationality").countrySelect();

        $("#address-country").countrySelect();

        $("#passport-country").countrySelect();
    });

$(document).ready(function () {
    const phoneInput = document.getElementById("phone");
    const emergencyPhoneInput = document.getElementById("emergency-phone");

    const phoneOptions = {
        initialCountry: "lb",
        separateDialCode: true,
        preferredCountries: ["lb", "us", "gb", "fr"],
        utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.1/build/js/utils.js"
    };

    if (phoneInput && typeof intlTelInput === "function") {
        const phoneIti = intlTelInput(phoneInput, phoneOptions);

        phoneInput.addEventListener("input", function () {
            document.getElementById("phone-full").value =
                phoneIti.getNumber();
        });

        phoneInput.addEventListener("countrychange", function () {
            document.getElementById("phone-full").value =
                phoneIti.getNumber();
        });
    }

    if (emergencyPhoneInput && typeof intlTelInput === "function") {
        const emergencyIti = intlTelInput(
            emergencyPhoneInput,
            phoneOptions
        );

        emergencyPhoneInput.addEventListener("input", function () {
            document.getElementById("emergency-phone-full").value =
                emergencyIti.getNumber();
        });

        emergencyPhoneInput.addEventListener("countrychange", function () {
            document.getElementById("emergency-phone-full").value =
                emergencyIti.getNumber();
        });
    }
});



})();

