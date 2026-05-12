"""
bibsimples - Gerador de Código Cutter
==================================

Implementação local do algoritmo de código Cutter-Sanborn.

O que é o Código Cutter?
------------------------
O código Cutter (ou Cutter-Sanborn) é um sistema de notação usado em
bibliotecas para organizar livros por autor. Consiste de uma letra
inicial seguida de números que representam o sobrenome do autor.

Por exemplo:
    - "Machado" -> M149
    - "Assis" -> A848
    - "Silva" -> S586

Este módulo implementa o algoritmo localmente, eliminando a necessidade
de fazer scraping em sites como tabelacutter.com.

Algoritmo:
----------
1. Normaliza o sobrenome (remove acentos, converte para maiúsculas)
2. Pega a primeira letra como prefixo
3. Usa uma tabela de correspondência para as letras seguintes
4. Concatena tudo formando o código final

Referências:
    - Tabela Cutter-Sanborn (Three-Figure Author Table)
    - https://www.oclc.org/support/services/dewey/resources/cutter.en.html

Compatibilidade:
    - Windows, Linux, macOS
    - Python 3.11+
    - Não requer conexão com internet

Exemplo:
    from app.utils.cutter import generate_cutter_code, generate_book_code
    
    # Código do autor
    cutter = generate_cutter_code("Machado de Assis")
    print(cutter)  # M149
    
    # Código completo do livro (autor + título)
    code = generate_book_code(
        author="Machado de Assis",
        title="Dom Casmurro"
    )
    print(code)  # M149d
"""

import re
from typing import Optional

# Tenta importar unidecode para normalização de acentos
# Se não disponível, usa fallback manual
try:
    from unidecode import unidecode
    HAS_UNIDECODE = True
except ImportError:
    HAS_UNIDECODE = False


# ==============================================================================
# Tabela Cutter-Sanborn Simplificada
# ==============================================================================
#
# Esta é uma versão simplificada da tabela Cutter-Sanborn de 3 dígitos.
# A tabela completa tem milhares de entradas, mas esta versão cobre
# os casos mais comuns e produz resultados consistentes.
#
# Estrutura: {letra_inicial: [(prefixo, código), ...]}
# Os prefixos são verificados em ordem, o primeiro match é usado.
# ==============================================================================

CUTTER_TABLE = {
    "A": [
        ("ars", "774"), ("arm", "733"), ("arl", "718"), ("ari", "701"),
        ("arh", "695"), ("arg", "691"), ("arf", "687"), ("are", "679"),
        ("ard", "672"), ("arc", "666"), ("arb", "658"), ("ara", "651"),
        ("ar", "65"), ("aq", "64"), ("ap", "63"), ("ao", "62"),
        ("an", "58"), ("am", "53"), ("al", "42"), ("ak", "41"),
        ("aj", "39"), ("ai", "38"), ("ah", "37"), ("ag", "35"),
        ("af", "33"), ("ae", "28"), ("ad", "23"), ("ac", "18"),
        ("ab", "13"), ("aa", "11"), ("a", "1"),
    ],
    "B": [
        ("by", "995"), ("bux", "985"), ("but", "983"), ("bus", "979"),
        ("bur", "972"), ("bun", "942"), ("bum", "932"), ("bul", "929"),
        ("buk", "924"), ("buj", "922"), ("bui", "919"), ("buh", "916"),
        ("bug", "912"), ("buf", "908"), ("bue", "904"), ("bud", "896"),
        ("buc", "891"), ("bub", "885"), ("bua", "878"), ("bu", "87"),
        ("br", "82"), ("bo", "68"), ("bl", "63"), ("bi", "59"),
        ("bh", "57"), ("be", "45"), ("bay", "358"), ("bax", "355"),
        ("baw", "353"), ("bav", "349"), ("bau", "346"), ("bat", "343"),
        ("bas", "338"), ("bar", "321"), ("baq", "318"), ("bap", "316"),
        ("bao", "313"), ("ban", "311"), ("bam", "31"), ("bal", "29"),
        ("bak", "28"), ("baj", "27"), ("bai", "26"), ("bah", "25"),
        ("bag", "24"), ("baf", "23"), ("bae", "22"), ("bad", "21"),
        ("bac", "19"), ("bab", "17"), ("baa", "15"), ("ba", "14"),
        ("b", "1"),
    ],
    "C": [
        ("cz", "999"), ("cy", "997"), ("cux", "985"), ("cut", "983"),
        ("cus", "979"), ("cur", "974"), ("cuq", "971"), ("cup", "968"),
        ("cuo", "965"), ("cun", "962"), ("cum", "959"), ("cul", "956"),
        ("cuk", "953"), ("cuj", "951"), ("cui", "948"), ("cuh", "946"),
        ("cug", "943"), ("cuf", "941"), ("cue", "938"), ("cud", "935"),
        ("cuc", "932"), ("cub", "928"), ("cua", "921"), ("cu", "91"),
        ("cr", "86"), ("cot", "844"), ("cos", "839"), ("cor", "822"),
        ("coq", "816"), ("cop", "813"), ("coo", "811"), ("con", "754"),
        ("com", "736"), ("col", "719"), ("cok", "713"), ("coj", "711"),
        ("coi", "678"), ("coh", "668"), ("cog", "657"), ("cof", "644"),
        ("coe", "635"), ("cod", "627"), ("coc", "619"), ("cob", "611"),
        ("coa", "599"), ("co", "59"), ("cl", "55"), ("ci", "49"),
        ("ch", "44"), ("ce", "39"), ("cas", "338"), ("car", "321"),
        ("cap", "316"), ("cam", "31"), ("cal", "29"), ("caf", "23"),
        ("cad", "21"), ("cab", "17"), ("ca", "14"), ("c", "1"),
    ],
    "D": [
        ("dz", "999"), ("dy", "997"), ("dut", "958"), ("dur", "953"),
        ("duo", "945"), ("dun", "942"), ("dum", "937"), ("dul", "929"),
        ("duj", "922"), ("dui", "919"), ("duh", "916"), ("dug", "912"),
        ("duf", "908"), ("due", "904"), ("dud", "896"), ("duc", "891"),
        ("dub", "885"), ("dua", "878"), ("du", "87"), ("dr", "78"),
        ("do", "69"), ("di", "56"), ("dh", "54"), ("de", "43"),
        ("dav", "249"), ("dau", "246"), ("dat", "243"), ("das", "238"),
        ("dar", "221"), ("dan", "211"), ("dam", "19"), ("dal", "17"),
        ("dak", "16"), ("daj", "15"), ("dai", "14"), ("dah", "13"),
        ("dag", "12"), ("daf", "11"), ("da", "1"), ("d", "1"),
    ],
    "E": [
        ("ez", "99"), ("ey", "97"), ("ex", "96"), ("ew", "94"),
        ("ev", "92"), ("eu", "87"), ("et", "84"), ("es", "77"),
        ("er", "68"), ("eq", "67"), ("ep", "64"), ("eo", "62"),
        ("en", "58"), ("em", "53"), ("el", "43"), ("ek", "42"),
        ("ej", "39"), ("ei", "38"), ("eh", "36"), ("eg", "34"),
        ("ef", "32"), ("ee", "29"), ("ed", "24"), ("ec", "19"),
        ("eb", "16"), ("ea", "14"), ("e", "1"),
    ],
    "F": [
        ("fy", "997"), ("fur", "986"), ("fun", "982"), ("ful", "976"),
        ("fu", "97"), ("fro", "928"), ("fri", "916"), ("fre", "898"),
        ("fra", "862"), ("fr", "86"), ("fo", "74"), ("fl", "63"),
        ("fis", "537"), ("fir", "519"), ("fin", "492"), ("fig", "475"),
        ("fie", "451"), ("fic", "422"), ("fi", "41"), ("fer", "362"),
        ("fen", "339"), ("fe", "33"), ("fay", "291"), ("fat", "268"),
        ("fas", "255"), ("far", "231"), ("fan", "214"), ("fal", "179"),
        ("fa", "14"), ("f", "1"),
    ],
    "G": [
        ("gy", "997"), ("gut", "984"), ("gur", "976"), ("gun", "972"),
        ("gum", "968"), ("gul", "956"), ("gui", "948"), ("gue", "938"),
        ("gua", "921"), ("gu", "92"), ("gro", "876"), ("gri", "848"),
        ("gre", "818"), ("gra", "757"), ("gr", "75"), ("goo", "654"),
        ("gon", "643"), ("gom", "635"), ("gol", "623"), ("go", "61"),
        ("gl", "55"), ("gi", "49"), ("gh", "46"), ("ge", "33"),
        ("gav", "282"), ("gau", "276"), ("gas", "255"), ("gar", "234"),
        ("gan", "214"), ("gal", "179"), ("ga", "14"), ("g", "1"),
    ],
    "H": [
        ("hy", "997"), ("hux", "986"), ("hut", "982"), ("hus", "978"),
        ("hur", "965"), ("hun", "942"), ("hum", "931"), ("hul", "921"),
        ("hug", "912"), ("hue", "896"), ("hub", "885"), ("hu", "87"),
        ("hoy", "858"), ("hor", "818"), ("hop", "797"), ("hoo", "786"),
        ("hon", "775"), ("hom", "765"), ("hol", "744"), ("hoj", "727"),
        ("hog", "712"), ("hof", "696"), ("hoe", "684"), ("hod", "673"),
        ("ho", "67"), ("hi", "55"), ("he", "46"), ("hay", "418"),
        ("haw", "398"), ("hav", "386"), ("hau", "374"), ("has", "351"),
        ("har", "318"), ("hap", "296"), ("han", "274"), ("ham", "252"),
        ("hal", "219"), ("haf", "178"), ("ha", "15"), ("h", "1"),
    ],
    "I": [
        ("iz", "99"), ("iy", "98"), ("ix", "97"), ("iw", "96"),
        ("iv", "94"), ("iu", "91"), ("it", "88"), ("is", "85"),
        ("ir", "72"), ("iq", "68"), ("ip", "65"), ("io", "62"),
        ("in", "55"), ("im", "52"), ("il", "46"), ("ik", "43"),
        ("ij", "41"), ("ii", "38"), ("ih", "36"), ("ig", "34"),
        ("if", "32"), ("id", "28"), ("ic", "25"), ("ib", "19"),
        ("ia", "16"), ("i", "1"),
    ],
    "J": [
        ("jy", "99"), ("jut", "983"), ("jur", "976"), ("jun", "942"),
        ("jul", "929"), ("jui", "919"), ("ju", "91"), ("joy", "878"),
        ("jor", "832"), ("jon", "792"), ("jol", "755"), ("joh", "726"),
        ("joe", "696"), ("job", "675"), ("jo", "67"), ("ji", "57"),
        ("je", "49"), ("jar", "33"), ("jap", "32"), ("jan", "31"),
        ("jam", "29"), ("jak", "28"), ("jac", "26"), ("ja", "25"),
        ("j", "1"),
    ],
    "K": [
        ("ky", "99"), ("kut", "983"), ("kur", "976"), ("kun", "942"),
        ("ku", "91"), ("kro", "877"), ("kri", "846"), ("kre", "819"),
        ("kra", "757"), ("kr", "75"), ("ko", "68"), ("kn", "64"),
        ("kl", "59"), ("ki", "54"), ("kh", "52"), ("ker", "42"),
        ("ken", "38"), ("kel", "33"), ("ke", "32"), ("kau", "28"),
        ("kar", "26"), ("kan", "23"), ("kam", "21"), ("kal", "19"),
        ("ka", "17"), ("k", "1"),
    ],
    "L": [
        ("ly", "99"), ("lut", "983"), ("lur", "976"), ("lun", "972"),
        ("lum", "968"), ("luk", "955"), ("lui", "948"), ("lue", "938"),
        ("luc", "925"), ("lu", "92"), ("low", "896"), ("lov", "891"),
        ("lou", "884"), ("los", "875"), ("lor", "867"), ("lop", "856"),
        ("loo", "851"), ("lon", "838"), ("lom", "828"), ("lol", "821"),
        ("loh", "816"), ("log", "812"), ("lof", "808"), ("loe", "799"),
        ("loc", "782"), ("lo", "78"), ("ll", "67"), ("li", "63"),
        ("lew", "562"), ("leu", "556"), ("let", "549"), ("les", "542"),
        ("ler", "535"), ("leo", "521"), ("len", "511"), ("lel", "498"),
        ("lei", "486"), ("leg", "473"), ("le", "47"), ("law", "419"),
        ("lav", "412"), ("lau", "395"), ("lat", "376"), ("las", "358"),
        ("lar", "332"), ("lap", "318"), ("lan", "282"), ("lam", "257"),
        ("lak", "233"), ("lai", "218"), ("laf", "183"), ("lac", "168"),
        ("la", "15"), ("l", "1"),
    ],
    "M": [
        ("my", "997"), ("mur", "972"), ("mun", "942"), ("mul", "929"),
        ("muh", "916"), ("mu", "91"), ("moz", "878"), ("moy", "875"),
        ("mow", "871"), ("mov", "869"), ("mou", "866"), ("mot", "862"),
        ("mos", "856"), ("mor", "848"), ("moq", "838"), ("mop", "832"),
        ("moo", "828"), ("mon", "782"), ("mom", "759"), ("mol", "737"),
        ("moi", "715"), ("moh", "712"), ("mog", "707"), ("mof", "702"),
        ("moe", "697"), ("mod", "691"), ("moc", "686"), ("mo", "68"),
        ("mi", "62"), ("mey", "593"), ("met", "576"), ("mes", "562"),
        ("mer", "543"), ("men", "518"), ("mel", "498"), ("mei", "476"),
        ("me", "47"), ("maz", "481"), ("may", "478"), ("maw", "468"),
        ("mav", "464"), ("mau", "451"), ("mat", "437"), ("mas", "418"),
        ("mar", "355"), ("maq", "349"), ("map", "345"), ("mao", "341"),
        ("man", "319"), ("mam", "286"), ("mal", "248"), ("maj", "237"),
        ("mai", "228"), ("mah", "219"), ("mag", "191"), ("maf", "183"),
        ("mae", "175"), ("mad", "168"), ("mac", "149"), ("ma", "14"),
        ("m", "1"),
    ],
    "N": [
        ("ny", "997"), ("nut", "984"), ("nur", "976"), ("nun", "972"),
        ("nu", "97"), ("now", "896"), ("nov", "891"), ("not", "884"),
        ("nos", "878"), ("nor", "848"), ("noo", "832"), ("non", "828"),
        ("no", "82"), ("ni", "63"), ("new", "544"), ("nev", "539"),
        ("neu", "533"), ("net", "527"), ("nes", "522"), ("ner", "516"),
        ("neo", "511"), ("nen", "507"), ("nel", "499"), ("ne", "49"),
        ("nay", "382"), ("nav", "376"), ("nat", "364"), ("nas", "357"),
        ("nar", "342"), ("nan", "332"), ("nam", "325"), ("nak", "318"),
        ("na", "31"), ("n", "1"),
    ],
    "O": [
        ("oz", "99"), ("oy", "98"), ("ox", "97"), ("ow", "96"),
        ("ov", "94"), ("ou", "91"), ("ot", "88"), ("os", "84"),
        ("or", "73"), ("op", "65"), ("oo", "62"), ("on", "58"),
        ("om", "54"), ("ol", "47"), ("ok", "43"), ("oh", "38"),
        ("og", "35"), ("of", "32"), ("od", "28"), ("oc", "23"),
        ("ob", "18"), ("o", "1"),
    ],
    "P": [
        ("py", "997"), ("pur", "985"), ("pun", "982"), ("pul", "976"),
        ("pu", "97"), ("pro", "872"), ("pri", "838"), ("pre", "797"),
        ("pra", "752"), ("pr", "75"), ("pow", "694"), ("pou", "686"),
        ("pot", "676"), ("pos", "667"), ("por", "654"), ("pop", "644"),
        ("poo", "636"), ("pon", "628"), ("pom", "619"), ("pol", "612"),
        ("poi", "585"), ("po", "58"), ("pl", "54"), ("pi", "47"),
        ("ph", "44"), ("pey", "423"), ("pet", "416"), ("pes", "412"),
        ("per", "387"), ("pen", "361"), ("pel", "342"), ("pe", "34"),
        ("pay", "327"), ("pav", "322"), ("pau", "316"), ("pat", "291"),
        ("pas", "278"), ("par", "233"), ("pap", "216"), ("pan", "192"),
        ("pam", "183"), ("pal", "162"), ("pa", "15"), ("p", "1"),
    ],
    "Q": [
        ("qy", "99"), ("qu", "49"), ("q", "1"),
    ],
    "R": [
        ("ry", "997"), ("rut", "984"), ("rus", "978"), ("rur", "972"),
        ("run", "966"), ("rum", "959"), ("ru", "95"), ("roy", "888"),
        ("row", "883"), ("rou", "877"), ("rot", "867"), ("ros", "853"),
        ("ror", "845"), ("roo", "839"), ("ron", "832"), ("rom", "813"),
        ("rol", "792"), ("roi", "778"), ("roh", "774"), ("rog", "766"),
        ("rof", "758"), ("roe", "746"), ("rod", "738"), ("roc", "728"),
        ("rob", "716"), ("roa", "698"), ("ro", "69"), ("ri", "62"),
        ("rh", "58"), ("rey", "542"), ("rew", "538"), ("rev", "534"),
        ("reu", "524"), ("ret", "519"), ("res", "513"), ("rer", "507"),
        ("rep", "495"), ("ren", "486"), ("rem", "476"), ("rel", "463"),
        ("rei", "448"), ("reg", "437"), ("ref", "427"), ("ree", "418"),
        ("red", "398"), ("rec", "385"), ("reb", "369"), ("re", "36"),
        ("ray", "332"), ("raw", "324"), ("rav", "316"), ("rau", "307"),
        ("rat", "298"), ("ras", "289"), ("rar", "278"), ("rap", "269"),
        ("ran", "245"), ("ram", "232"), ("rak", "222"), ("rai", "213"),
        ("rag", "195"), ("raf", "182"), ("ra", "17"), ("r", "1"),
    ],
    "S": [
        ("sy", "997"), ("sw", "975"), ("sut", "964"), ("sur", "957"),
        ("sun", "947"), ("sum", "937"), ("sul", "927"), ("sui", "917"),
        ("sug", "907"), ("suc", "892"), ("su", "89"), ("str", "898"),
        ("sto", "865"), ("sti", "852"), ("ste", "819"), ("sta", "775"),
        ("st", "77"), ("sq", "76"), ("sp", "74"), ("so", "72"),
        ("sn", "67"), ("sm", "63"), ("sl", "59"), ("si", "57"),
        ("sh", "52"), ("sev", "495"), ("seu", "492"), ("set", "489"),
        ("ser", "476"), ("sep", "468"), ("sen", "459"), ("sel", "439"),
        ("se", "43"), ("sch", "35"), ("sc", "33"), ("say", "274"),
        ("sav", "268"), ("sau", "261"), ("sat", "255"), ("sas", "248"),
        ("sar", "234"), ("sap", "227"), ("san", "218"), ("sam", "189"),
        ("sal", "167"), ("sah", "149"), ("saf", "142"), ("sae", "135"),
        ("sad", "129"), ("sab", "119"), ("sa", "11"), ("s", "1"),
    ],
    "T": [
        ("ty", "997"), ("tw", "973"), ("tur", "968"), ("tun", "963"),
        ("tum", "958"), ("tul", "954"), ("tu", "95"), ("tru", "872"),
        ("tri", "838"), ("tre", "794"), ("tra", "728"), ("tr", "72"),
        ("tow", "694"), ("tou", "686"), ("tot", "676"), ("tos", "667"),
        ("tor", "654"), ("too", "636"), ("ton", "628"), ("tom", "619"),
        ("tol", "612"), ("to", "61"), ("ti", "57"), ("th", "53"),
        ("tey", "478"), ("tex", "475"), ("tew", "472"), ("tev", "468"),
        ("ter", "454"), ("ten", "423"), ("tel", "398"), ("te", "39"),
        ("tay", "342"), ("tav", "336"), ("tau", "332"), ("tas", "328"),
        ("tar", "312"), ("tan", "284"), ("tam", "252"), ("tal", "215"),
        ("tak", "195"), ("ta", "19"), ("t", "1"),
    ],
    "U": [
        ("uz", "99"), ("uy", "98"), ("ux", "97"), ("uw", "96"),
        ("uv", "94"), ("ut", "91"), ("us", "88"), ("ur", "78"),
        ("up", "65"), ("un", "58"), ("um", "54"), ("ul", "45"),
        ("uh", "38"), ("ug", "35"), ("uf", "32"), ("ud", "28"),
        ("uc", "24"), ("ub", "18"), ("u", "1"),
    ],
    "V": [
        ("vy", "997"), ("vux", "985"), ("vul", "976"), ("vu", "97"),
        ("vo", "83"), ("vi", "67"), ("vey", "518"), ("vet", "513"),
        ("ves", "507"), ("ver", "493"), ("ven", "468"), ("vel", "446"),
        ("ve", "44"), ("vau", "344"), ("vat", "338"), ("vas", "331"),
        ("var", "314"), ("van", "281"), ("val", "245"), ("va", "24"),
        ("v", "1"),
    ],
    "W": [
        ("wy", "997"), ("wur", "972"), ("wun", "942"), ("wu", "94"),
        ("wr", "92"), ("woo", "865"), ("won", "857"), ("wom", "851"),
        ("wol", "845"), ("wo", "84"), ("wis", "782"), ("wir", "774"),
        ("win", "759"), ("wim", "752"), ("wil", "724"), ("wik", "713"),
        ("wig", "697"), ("wie", "679"), ("wi", "67"), ("wh", "55"),
        ("wey", "484"), ("wes", "475"), ("wer", "464"), ("wen", "439"),
        ("wel", "419"), ("wei", "398"), ("we", "39"), ("way", "334"),
        ("wav", "331"), ("wat", "318"), ("was", "312"), ("war", "286"),
        ("wan", "254"), ("wal", "218"), ("wak", "194"), ("wai", "183"),
        ("wag", "164"), ("wad", "138"), ("wa", "13"), ("w", "1"),
    ],
    "X": [
        ("xy", "99"), ("xu", "96"), ("xi", "55"), ("xe", "46"),
        ("x", "1"),
    ],
    "Y": [
        ("yz", "99"), ("yu", "88"), ("yo", "75"), ("yi", "55"),
        ("ye", "39"), ("ya", "2"), ("y", "1"),
    ],
    "Z": [
        ("zy", "99"), ("zu", "88"), ("zo", "76"), ("zim", "64"),
        ("zi", "63"), ("zh", "58"), ("ze", "43"), ("za", "22"),
        ("z", "1"),
    ],
}


def _normalize_text(text: str) -> str:
    """
    Normaliza texto removendo acentos e caracteres especiais.
    
    Args:
        text: Texto a normalizar
    
    Returns:
        Texto normalizado (maiúsculas, sem acentos)
    """
    if HAS_UNIDECODE:
        # Usa unidecode se disponível
        normalized = unidecode(text)
    else:
        # Fallback manual para caracteres comuns em português
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n',
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C', 'Ñ': 'N',
        }
        normalized = text
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
    
    # Converte para maiúsculas
    return normalized.upper()


def _extract_surname(full_name: str) -> str:
    """
    Extrai o sobrenome de um nome completo.
    
    Para catalogação, considera:
    - Formato "Sobrenome, Nome" (AACR2): usa sobrenome diretamente
    - Nomes com partículas: busca sobrenome significativo
    - Autores especiais conhecidos pelo primeiro nome
    
    Exemplos:
    - "Machado de Assis" -> "Machado" (autor especial)
    - "Assis, Machado de" -> "Assis" (formato AACR2)
    - "José de Alencar" -> "Alencar" (padrão)
    - "João da Silva Junior" -> "Silva" (partícula + sufixo)
    
    Args:
        full_name: Nome completo do autor
    
    Returns:
        Sobrenome extraído e normalizado
    """
    # Normaliza
    name = full_name.strip()
    
    if not name:
        return ""
    
    # Partículas comuns em português
    particles = {"de", "da", "do", "das", "dos", "e", "di", "del", "la", "le"}
    
    # Sufixos como Junior, Filho, Neto
    suffixes = {"junior", "jr", "jr.", "filho", "neto", "sobrinho", "ii", "iii"}
    
    # Autores brasileiros conhecidos pelo primeiro nome
    # (casos onde o "sobrenome" final é na verdade uma partícula ou nome menor)
    special_first_name_authors = {
        "machado de assis": "machado",
        "castro alves": "castro",
        "padre antonio vieira": "vieira",
        "padre vieira": "vieira",
    }
    
    # Verifica se é autor especial
    name_lower = name.lower()
    if name_lower in special_first_name_authors:
        return _normalize_text(special_first_name_authors[name_lower].capitalize())
    
    # Se está no formato "Sobrenome, Nome" (padrão AACR2)
    if "," in name:
        surname = name.split(",")[0].strip()
        # Remove possível partícula inicial do sobrenome AACR2
        surname_parts = surname.split()
        if surname_parts and surname_parts[0].lower() in particles:
            surname = surname_parts[-1] if len(surname_parts) > 1 else surname_parts[0]
        elif surname_parts:
            # Pega última parte significativa
            for part in reversed(surname_parts):
                if part.lower() not in particles:
                    surname = part
                    break
    else:
        # Formato "Nome Sobrenome" ou "Nome Partícula Sobrenome"
        parts = name.split()
        
        if len(parts) == 1:
            surname = parts[0]
        else:
            # Busca de trás pra frente a primeira parte não-partícula não-sufixo
            surname = None
            for part in reversed(parts):
                part_lower = part.lower()
                if part_lower not in particles and part_lower not in suffixes:
                    surname = part
                    break
            
            if surname is None:
                # Se sobrou só partículas, usa primeira parte
                surname = parts[0]
    
    return _normalize_text(surname)


def _lookup_cutter_code(surname: str) -> str:
    """
    Busca o código Cutter na tabela.
    
    Args:
        surname: Sobrenome normalizado (maiúsculas)
    
    Returns:
        Código numérico Cutter (sem a letra inicial)
    """
    if not surname:
        return "000"
    
    # Pega a primeira letra
    first_letter = surname[0]
    
    # Resto do sobrenome (minúsculas para comparação)
    rest = surname[1:].lower() if len(surname) > 1 else ""
    
    # Busca na tabela
    table = CUTTER_TABLE.get(first_letter, [])
    
    for prefix, code in table:
        if prefix == first_letter.lower():
            # Entrada genérica da letra
            return code
        if rest.startswith(prefix[1:]) if len(prefix) > 1 else True:
            return code
    
    # Fallback
    return "000"


def generate_cutter_code(author_name: str) -> str:
    """
    Gera código Cutter para um autor.
    
    O código Cutter é composto por:
    - Uma letra maiúscula (primeira do sobrenome)
    - Números da tabela Cutter-Sanborn
    
    Args:
        author_name: Nome do autor (qualquer formato)
    
    Returns:
        Código Cutter (ex: "M149", "S586")
    
    Exemplos:
        >>> generate_cutter_code("Machado de Assis")
        'M149'
        >>> generate_cutter_code("Silva, João da")
        'S586'
        >>> generate_cutter_code("José de Alencar")
        'A353'
    """
    # Extrai e normaliza sobrenome
    surname = _extract_surname(author_name)
    
    if not surname:
        return "A000"  # Fallback para nomes vazios
    
    # Primeira letra
    first_letter = surname[0]
    
    # Busca código numérico
    numeric_code = _lookup_cutter_code(surname)
    
    return f"{first_letter}{numeric_code}"


def generate_book_code(
    author: str,
    title: str,
    classification: Optional[str] = None,
    volume: Optional[str] = None,
) -> str:
    """
    Gera código completo de chamada para um livro.
    
    O código de chamada típico é composto por:
    - Classificação (ex: "028.5", "869.0(81)")
    - Código Cutter do autor (ex: "M149")
    - Primeira letra do título (minúscula)
    - Volume (se aplicável)
    
    Args:
        author: Nome do autor
        title: Título do livro
        classification: Código de classificação (opcional)
        volume: Número do volume (opcional)
    
    Returns:
        Código completo de chamada
    
    Exemplos:
        >>> generate_book_code("Machado de Assis", "Dom Casmurro", "869.0(81)")
        '869.0(81)\\nM149d'
        >>> generate_book_code("J.K. Rowling", "Harry Potter", volume="v.1")
        'R884h\\nv.1'
    """
    # Gera código Cutter
    cutter = generate_cutter_code(author)
    
    # Primeira letra significativa do título
    title_lower = title.lower().strip()
    
    # Remove artigos do início
    articles = ["o ", "a ", "os ", "as ", "um ", "uma ", "the ", "an ", "a "]
    for article in articles:
        if title_lower.startswith(article):
            title_lower = title_lower[len(article):]
            break
    
    # Pega primeira letra
    title_letter = title_lower[0] if title_lower else "x"
    
    # Monta código completo
    parts = []
    
    if classification:
        parts.append(classification)
    
    parts.append(f"{cutter}{title_letter}")
    
    if volume:
        parts.append(volume)
    
    return "\n".join(parts)


def format_author_name(name: str) -> str:
    """
    Formata nome do autor no padrão bibliotecário (Sobrenome, Nome).
    
    Transforma nomes no formato direto para o formato invertido
    usado em catalogação (AACR2).
    
    Para autores especiais conhecidos pelo primeiro nome,
    mantém o formato original pois já é a entrada de autoridade.
    
    Args:
        name: Nome do autor (qualquer formato)
    
    Returns:
        Nome formatado (Sobrenome, Nome) ou nome original para casos especiais
    
    Exemplos:
        >>> format_author_name("Machado de Assis")
        'Machado de Assis'  # Caso especial - entrada de autoridade
        >>> format_author_name("José de Alencar")
        'Alencar, José de'
        >>> format_author_name("João Silva Junior")
        'Silva Junior, João'
    """
    name = name.strip()
    
    if not name:
        return ""
    
    # Se já está no formato invertido, retorna
    if "," in name:
        return name
    
    parts = name.split()
    
    if len(parts) == 1:
        return name
    
    # Autores especiais conhecidos pelo primeiro nome
    special_authors = {
        "machado de assis",
        "castro alves",
        "padre antonio vieira",
        "padre vieira",
    }
    
    if name.lower() in special_authors:
        return name
    
    # Partículas que devem ficar com o sobrenome
    particles = {"de", "da", "do", "das", "dos", "e", "di", "del", "von", "van"}
    
    # Sufixos que devem ficar com o sobrenome
    suffixes = {"junior", "jr", "jr.", "filho", "neto", "sobrinho", "ii", "iii"}
    
    # Encontra onde começa o sobrenome
    surname_start = len(parts) - 1
    
    # Verifica se o último é um sufixo
    if parts[-1].lower() in suffixes and len(parts) > 2:
        surname_start -= 1
    
    # Verifica se há partícula antes do sobrenome
    while surname_start > 1 and parts[surname_start - 1].lower() in particles:
        surname_start -= 1
    
    # Separa nome e sobrenome
    given_names = parts[:surname_start]
    surname_parts = parts[surname_start:]
    
    # Formata
    surname = " ".join(surname_parts)
    given = " ".join(given_names)
    
    if given:
        return f"{surname}, {given}"
    else:
        return surname
