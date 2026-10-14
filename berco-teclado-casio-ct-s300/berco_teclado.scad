// Berço para Casio CT-S300 em suporte X
// Cola-se a face plana (topo) no fundo do teclado com fita dupla face;
// o canal de baixo encaixa sobre o braço do suporte e impede o teclado de escorregar.
// Abra no OpenSCAD (ou no Customizer do MakerWorld/Thingiverse), ajuste e exporte STL.

/* [Braço do suporte — MEÇA o seu, incluindo a espuma/borracha] */
formato = "redondo"; // [redondo, quadrado]
diametro_braco = 30;   // mm (largura do tubo, se quadrado)
folga = 1.0;           // mm, folga total no canal

/* [Peça] */
comprimento = 60;      // mm, ao longo do braço
parede = 5;            // mm, paredes laterais
espessura_topo = 4;    // mm, acima do canal (face colada)
profundidade = 0.5;    // fração do braço que entra no canal (0.3–0.6)
chanfro_entrada = 1.5; // mm

$fn = 96;
r  = diametro_braco/2 + folga/2;
W  = 2*r + 2*parede;
hc = profundidade * 2*r;
H  = hc + espessura_topo;

module perfil() {
    difference() {
        offset(r=1) offset(delta=-1) translate([-W/2, 0]) square([W, H]);
        if (formato == "redondo") {
            translate([0, hc - r]) circle(r);
        } else {
            translate([-r, -1]) square([2*r, hc + 1]);
        }
        // chanfro na entrada do canal
        polygon([[-r - chanfro_entrada, -0.01], [-r, chanfro_entrada],
                 [ r, chanfro_entrada], [ r + chanfro_entrada, -0.01]]);
    }
}

// Impressão: no fatiador, deite a peça com a face colada (topo plano) na mesa.
rotate([90, 0, 0]) linear_extrude(comprimento) perfil();
