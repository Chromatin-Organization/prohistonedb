// PhyD3 phylogenetic tree viewer
const phyd3Container = document.querySelector("#phyd3-container");

const opts = {
    dynamicHide: true,
    height: 1200,
    invertColors: false,
    lineupNodes: true,
    showDomains: true,
    showDomainNames: false,
    showDomainColors: true,
    showGraphs: true,
    showGraphLegend: true,
    showSupportValues: false,
    maxDecimalsSupportValues: 1,
    showLengthValues: false,
    maxDecimalsLengthValues: 3,
    showLength: false,
    showNodeNames: true,
    showNodesType: "all",
    showPhylogram: false,
    showTaxonomy: true,
    showFullTaxonomy: true,
    showSequences: false,
    showTaxonomyColors: true,
    backgroundColor: "#ffffff",
    foregroundColor: "#000000",
};

function loadPhyloTree() {
    d3.xml(phyd3xml, function(xml) {
        const tree = phyd3.phyloxml.parse(xml);
        phyd3.phylogram.build(phyd3Container, tree, opts);
    });
}

loadPhyloTree();