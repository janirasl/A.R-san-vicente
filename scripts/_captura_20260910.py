"""
Genera idealista_san_vicente_raw_2026-09-10.csv a partir de la extraccion por DOM.

Novedad importante de esta captura frente a las de agosto: se captura el
ID DE ANUNCIO de Idealista (el numero de /inmueble/NNNNNNN/). Eso permite
emparejar capturas sucesivas de forma EXACTA, sin la heuristica de
precio+habitaciones+m2 que hubo que usar hasta ahora.

Tambien se captura 'antiguedad_anuncio', el indicador de recencia que Idealista
muestra en algunos anuncios ("7 horas", "2 minutos"). Ojo: marca cuando se
ACTUALIZO el anuncio, no cuando se publico, y solo aparece en los recientes.
"""

import io
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent

# id;precio;habitaciones;m2;zona;planta;ascensor;tag_temporada;antiguedad
CRUDO = {
1: """112508781;990;3;104;Centro;4ª planta;si;temporada;7 horas
112363779;1000;3;75;Centro;1ª planta;no;;
112492572;850;3;83;;1ª planta;no;temporada;
104856742;1050;3;95;Centro;3ª planta;no;temporada;
112491266;1100;4;116;;;;;
112288930;990;3;92;Centro;3ª planta;no;temporada;2 minutos
112460345;1100;4;145;Alcalde Felipe Mallol;3ª planta;si;;
112365401;1000;4;110;Centro;1ª planta;no;temporada;
112079183;900;3;117;Alcalde Felipe Mallol;3ª planta;no;temporada;
112474042;1150;6;200;Centro;;;temporada;
111950477;900;4;100;Centro;3ª planta;si;temporada;
112091993;1100;4;110;Centro;3ª planta;no;temporada;
111974442;700;;45;Alcalde Felipe Mallol;1ª planta;no;temporada;
112472408;3200;5;250;Los Girasoles;;;temporada;
112435993;900;3;90;Centro;1ª planta;si;;
108392486;980;4;111;Alcalde Felipe Mallol;3ª planta;no;temporada;
112491229;1200;4;116;;;;temporada;
108615751;900;4;140;;4ª planta;no;;
98416215;1000;4;110;Centro;6ª planta;si;temporada;
105831233;1000;4;120;Centro;2ª planta;si;temporada;
112404446;1290;3;90;Sol y Luz;5ª planta;si;;
112258283;1100;2;80;;5ª planta;si;;
111631072;1300;4;124;Los Girasoles;1ª planta;si;;
112456969;1600;4;140;Villamontes-Boqueres;;;temporada;
112473894;1000;3;80;Centro;4ª planta;si;temporada;
112310566;1050;4;126;;3ª planta;si;;
112335464;850;3;82;Centro;3ª planta;no;temporada;
112367343;860;4;137;Centro;1ª planta;si;temporada;
112360915;1100;4;112;Centro;3ª planta;no;temporada;
111697774;900;3;130;Centro;1ª planta;no;temporada;""",

2: """112275746;1100;4;111;;3ª planta;si;;
102020896;1500;5;100;Centro;3ª planta;no;temporada;
98359478;900;3;90;Centro;2ª planta;no;temporada;
112382424;1150;3;80;;;;temporada;
112075109;900;3;90;;3ª planta;no;temporada;
105885500;920;3;100;Centro;4ª planta;no;temporada;
94925525;890;4;90;Centro;1ª planta;si;temporada;
112054915;1750;5;100;Centro;2ª planta;si;temporada;
112156668;1000;3;95;Centro;1ª planta;si;temporada;
108899268;900;3;90;Alcalde Felipe Mallol;3ª planta;si;temporada;
112238150;990;3;95;Centro;4ª planta;si;temporada;
112395024;800;3;65;Haygon - Universidad;1ª planta;no;temporada;
111306537;1520;1;98;Centro;Bajo;no;temporada;
112382302;1200;4;100;Centro;Bajo;si;temporada;
98218271;840;3;95;Centro;3ª planta;si;temporada;
107741698;1000;4;120;Los Girasoles;3ª planta;si;temporada;
112222845;800;3;106;Centro;4ª planta;si;temporada;
112279039;900;3;90;;;;;
111961649;825;3;100;Centro;6ª planta;si;temporada;
112251416;2400;4;500;Villamontes-Boqueres;;;;
105191370;1500;4;110;Centro;Entreplanta;si;temporada;
111587247;1350;3;160;Centro;;;;
111764464;1050;3;112;;;;temporada;
112258110;1400;5;120;Centro;2ª planta;no;temporada;
112446974;1100;3;120;Centro;2ª planta;si;;
112337892;1100;4;152;Centro;1ª planta;si;temporada;
112086553;630;;42;Centro;1ª planta;si;temporada;
112393388;960;3;100;Alcalde Felipe Mallol;2ª planta;si;temporada;
112082386;800;2;75;Centro;1ª planta;si;temporada;
111984769;900;3;100;Centro;4ª planta;si;;""",

3: """112076150;630;;42;Centro;1ª planta;si;temporada;
108948979;1300;3;100;;;;;
81717288;810;3;90;Centro;3ª planta;si;temporada;
112339175;800;3;115;Centro;1ª planta;si;temporada;
112237069;1200;4;121;Centro;2ª planta;si;temporada;
112225609;990;3;110;Alcalde Felipe Mallol;5ª planta;si;temporada;
112434975;840;3;90;Centro;2ª planta;no;temporada;
112453420;1050;3;90;Centro;3ª planta;si;temporada;
112372116;1550;3;90;Sol y Luz;3ª planta;si;;
112442856;875;2;76;Centro;Bajo;si;;
112343782;1200;4;110;Centro;2ª planta;si;temporada;
98115702;1250;5;200;;;;;
112414666;925;2;80;Centro;Bajo;si;temporada;
110841602;750;1;30;Villamontes-Boqueres;;;temporada;
111879521;1300;4;100;;;;;
105997520;1200;3;129;Centro;4ª planta;si;temporada;
94575384;1100;3;90;Sol y Luz;3ª planta;si;;
111688370;800;3;85;Centro;Bajo;no;temporada;
108923012;900;3;85;;1ª planta;no;;
86641820;810;3;90;Centro;1ª planta;no;temporada;
100645240;880;4;90;Centro;1ª planta;no;temporada;
108495799;1350;3;170;Centro;Bajo;si;;
108808460;960;3;95;Centro;3ª planta;no;temporada;
105549393;1000;3;90;Centro;2ª planta;si;temporada;
112146951;850;3;95;Centro;1ª planta;no;;
103098615;870;2;85;;1ª planta;si;temporada;
112112345;850;3;95;Centro;3ª planta;si;temporada;
112235045;1000;4;97;Alcalde Felipe Mallol;2ª planta;no;temporada;
112269756;1300;4;120;Centro;1ª planta;si;;
112057741;1100;2;120;;1ª planta;si;temporada;""",
}

CABECERA = ("fecha_captura,fuente,pagina,id_anuncio,titulo,precio_mes_eur,habitaciones,"
            "superficie_m2,zona,planta,ascensor,antiguedad_anuncio,descripcion_resumida,url_fuente")


def main():
    filas = [CABECERA]
    total = 0
    for pagina, bloque in CRUDO.items():
        for linea in bloque.strip().split("\n"):
            idA, precio, hab, m2, zona, planta, ascensor, tag, antig = linea.split(";")
            desc = "Alquiler de temporada" if tag else ""
            # el titulo no se conserva literal: esta captura se hizo leyendo el DOM.
            # A cambio queda el ID, que permite ir al anuncio original y emparejar
            # capturas de forma exacta -> mejor trazabilidad que el titulo.
            titulo = f"Anuncio {idA}" + (f" ({zona})" if zona else "")
            url = f"https://www.idealista.com/inmueble/{idA}/"
            filas.append(",".join([
                "2026-09-10", "Idealista", f"p{pagina}", idA, titulo, precio, hab,
                m2, zona, planta, ascensor, antig, desc, url,
            ]))
            total += 1

    destino = RAW_DIR / "idealista_san_vicente_raw_2026-09-10.csv"
    io.open(destino, "w", encoding="utf-8").write("\n".join(filas) + "\n")
    print(f"{total} anuncios -> {destino}")


if __name__ == "__main__":
    main()
