const myViewer = document.querySelector("#mspViewer");
const demoURL = "/static/data/A0A7K4BZ95/A0A7K4BZ95_tetramer/A0A7K4BZ95_unrelaxed_rank_1_model_4.pdb";

molstar.Viewer.create('mspViewer', {
    // https://molstar.org/docs/plugin/
    // https://molstar.org/viewer-docs/query-parameters/
    // https://github.com/molstar/pdbe-molstar/blob/master/index.html

    layoutIsExpanded: false, // expand to window
    layoutShowControls: true, // rightsidebar & sequence panel
    layoutShowRemoteState: false,
    layoutShowSequence: true,
    layoutShowLog: false,
    layoutShowLeftPanel: false,
    alphafoldView: true,

    // show/hide viewport buttons
    viewportShowExpand: true,
    viewportShowSelectionMode: false,
    viewportShowAnimation: false,
    viewportShowControls: false // control panel (= rightsidebar & sequence panel) toggle
}).then(viewer => {
    viewer.loadStructureFromUrl(demoURL, format='pdb');
});