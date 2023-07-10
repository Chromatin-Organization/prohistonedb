// Skylign sequence alignment viewer
const logoContainer = document.querySelector("#logo-container");

async function getHMMJSON() {
    // HMMJSONurl defined in entry/categories pages
    const response = await fetch(HMMJSONurl);
    const json = await response.json();
    const HMMStringified = JSON.stringify(json);

    return HMMStringified;
}

async function setHMMJSON() { 
    logoContainer.setAttribute('data-logo', await getHMMJSON());
}

async function addLogo() {
    await setHMMJSON();
    $(logoContainer).hmm_logo({column_width: 34, height_toggle: 'enabled', column_info: '#logo_info',  zoom: 1});

    // add some class(es)
    const logoFormFieldset = document.querySelector(".logo_form fieldset");
    logoFormFieldset.classList.add("py-3", "input-group", "input-group-sm", "w-40");

    const logoInput = document.querySelector(".logo_position");
    logoInput.classList.add("form-control", "bg-light", "ms-2", "rounded-start");

    const logoGoBtn = document.querySelector(".logo_change");
    logoGoBtn.classList.add("btn", "btn-sm", "btn-secondary", "mb-0", "rounded-end");
    
    const logoSettingsBtn = document.querySelector(".logo_settings_switch");
    logoSettingsBtn.classList.add("btn", "btn-sm", "btn-secondary");

    // #logo_info is a non-responsive table, so add a scrollbar
    const categoryScroll = new PerfectScrollbar("#logo_info");
}

addLogo();