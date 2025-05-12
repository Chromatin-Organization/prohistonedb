// PhyD3 phylogenetic tree viewer
const phyd3Container = document.querySelector("#phyd3-container");

function loadPhyloTree() {
    d3.xml(phyd3xml, function(xml) {
        const tree = phyd3.phyloxml.parse(xml);
        phyd3.phylogram.build(phyd3Container, tree, {});
    });
}

loadPhyloTree();