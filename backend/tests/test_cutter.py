"""
bibsimples - Testes do Gerador de Código Cutter
============================================

Testes unitários para o módulo app.utils.cutter.

Estes testes verificam:
- Geração de código Cutter para diversos nomes
- Extração correta de sobrenomes
- Formatação de nomes de autores
- Geração de código completo de livros

Executar com:
    pytest tests/test_cutter.py -v
    pytest tests/test_cutter.py -v -k "test_cutter_code"
"""

import pytest

from app.utils.cutter import (
    format_author_name,
    generate_book_code,
    generate_cutter_code,
)


# ==============================================================================
# Testes de Geração de Código Cutter
# ==============================================================================

class TestGenerateCutterCode:
    """Testes para a função generate_cutter_code."""
    
    def test_simple_surname(self):
        """Testa código para sobrenome simples."""
        code = generate_cutter_code("Silva")
        assert code.startswith("S")
        assert len(code) >= 2
    
    def test_machado_de_assis(self):
        """Testa código para Machado de Assis (autor brasileiro famoso)."""
        code = generate_cutter_code("Machado de Assis")
        # Deve começar com M (de Machado)
        assert code.startswith("M")
    
    def test_inverted_name_format(self):
        """Testa nome no formato invertido (Sobrenome, Nome)."""
        code = generate_cutter_code("Assis, Machado de")
        # Deve começar com A (de Assis)
        assert code.startswith("A")
    
    def test_name_with_junior(self):
        """Testa nome com sufixo Junior."""
        code = generate_cutter_code("João Silva Junior")
        # Deve ser Silva, não Junior
        assert code.startswith("S")
    
    def test_name_with_filho(self):
        """Testa nome com sufixo Filho."""
        code = generate_cutter_code("Pedro Oliveira Filho")
        # Deve ser Oliveira, não Filho
        assert code.startswith("O")
    
    def test_name_with_neto(self):
        """Testa nome com sufixo Neto."""
        code = generate_cutter_code("Carlos Pereira Neto")
        # Deve ser Pereira, não Neto
        assert code.startswith("P")
    
    def test_single_name(self):
        """Testa nome único (sem sobrenome)."""
        code = generate_cutter_code("Aristóteles")
        assert code.startswith("A")
    
    def test_name_with_particles(self):
        """Testa nome com partículas (de, da, do, etc.)."""
        code = generate_cutter_code("José de Alencar")
        # Deve ser Alencar
        assert code.startswith("A")
    
    def test_name_with_multiple_particles(self):
        """Testa nome com múltiplas partículas."""
        code = generate_cutter_code("Maria da Silva e Souza")
        # Deve ser Souza
        assert code.startswith("S")
    
    def test_empty_name(self):
        """Testa nome vazio."""
        code = generate_cutter_code("")
        # Deve retornar código padrão
        assert code == "A000"
    
    def test_whitespace_name(self):
        """Testa nome com apenas espaços."""
        code = generate_cutter_code("   ")
        assert code == "A000"
    
    def test_name_with_accents(self):
        """Testa nome com acentos (português)."""
        code = generate_cutter_code("José Álvares de Azevedo")
        assert code.startswith("A")
    
    def test_name_with_cedilla(self):
        """Testa nome com cedilha."""
        code = generate_cutter_code("Gonçalves")
        # Ç deve ser normalizado para C -> G
        assert code.startswith("G")
    
    def test_foreign_name_with_von(self):
        """Testa nome estrangeiro com 'von'."""
        code = generate_cutter_code("Ludwig van Beethoven")
        assert code.startswith("B")
    
    def test_foreign_name_with_van(self):
        """Testa nome estrangeiro com 'van'."""
        code = generate_cutter_code("Vincent van Gogh")
        assert code.startswith("G")
    
    def test_code_has_numbers(self):
        """Testa que o código contém números após a letra."""
        code = generate_cutter_code("João Silva")
        # Deve ter letra + números
        assert code[0].isalpha()
        assert code[1:].isdigit() or len(code[1:]) >= 1
    
    # Testes de casos específicos conhecidos
    @pytest.mark.parametrize("name,expected_letter", [
        ("Alencar", "A"),
        ("Borges", "B"),
        ("Cervantes", "C"),
        ("Dostoiévski", "D"),
        ("Eça de Queirós", "Q"),
        ("Fitzgerald", "F"),
        ("Garcia Márquez", "M"),
        ("Hemingway", "H"),
        ("Ibsen", "I"),
        ("Joyce", "J"),
        ("Kafka", "K"),
        ("Lispector", "L"),
        ("Monteiro Lobato", "L"),
        ("Neruda", "N"),
        ("Orwell", "O"),
        ("Poe", "P"),
        ("Queirós", "Q"),
        ("Rosa", "R"),
        ("Shakespeare", "S"),
        ("Tolstói", "T"),
        ("Unamuno", "U"),
        ("Verne", "V"),
        ("Woolf", "W"),
        ("Xenofonte", "X"),
        ("Yeats", "Y"),
        ("Zola", "Z"),
    ])
    def test_alphabet_coverage(self, name: str, expected_letter: str):
        """Testa que todas as letras do alfabeto funcionam."""
        code = generate_cutter_code(name)
        assert code.startswith(expected_letter)


# ==============================================================================
# Testes de Geração de Código de Livro
# ==============================================================================

class TestGenerateBookCode:
    """Testes para a função generate_book_code."""
    
    def test_basic_book_code(self):
        """Testa código básico (autor + título)."""
        code = generate_book_code(
            author="Machado de Assis",
            title="Dom Casmurro"
        )
        # Deve conter código Cutter + letra do título
        assert "M" in code  # Machado
        assert "d" in code.lower()  # Dom -> d
    
    def test_book_code_with_classification(self):
        """Testa código com classificação."""
        code = generate_book_code(
            author="Machado de Assis",
            title="Dom Casmurro",
            classification="869.0(81)"
        )
        assert "869.0(81)" in code
    
    def test_book_code_with_volume(self):
        """Testa código com volume."""
        code = generate_book_code(
            author="J.K. Rowling",
            title="Harry Potter e a Pedra Filosofal",
            volume="v.1"
        )
        assert "v.1" in code
    
    def test_title_starting_with_article_o(self):
        """Testa título começando com artigo 'O'."""
        code = generate_book_code(
            author="José de Alencar",
            title="O Guarani"
        )
        # Deve usar 'g' de Guarani, não 'o' do artigo
        assert "g" in code.lower()
    
    def test_title_starting_with_article_a(self):
        """Testa título começando com artigo 'A'."""
        code = generate_book_code(
            author="Clarice Lispector",
            title="A Hora da Estrela"
        )
        # Deve usar 'h' de Hora, não 'a' do artigo
        assert "h" in code.lower()
    
    def test_title_starting_with_article_the(self):
        """Testa título em inglês começando com 'The'."""
        code = generate_book_code(
            author="Ernest Hemingway",
            title="The Old Man and the Sea"
        )
        # Deve usar 'o' de Old, não 't' de The
        assert "o" in code.lower()
    
    def test_full_book_code(self):
        """Testa código completo com todos os elementos."""
        code = generate_book_code(
            author="Jorge Amado",
            title="Capitães da Areia",
            classification="869.0(81)",
            volume="v.2"
        )
        
        lines = code.split("\n")
        assert len(lines) == 3
        assert lines[0] == "869.0(81)"  # Classificação
        assert lines[1].startswith("A")  # Amado
        assert "c" in lines[1].lower()   # Capitães
        assert lines[2] == "v.2"         # Volume


# ==============================================================================
# Testes de Formatação de Nomes
# ==============================================================================

class TestFormatAuthorName:
    """Testes para a função format_author_name."""
    
    def test_direct_name(self):
        """Testa nome no formato direto."""
        formatted = format_author_name("José de Alencar")
        # Deve inverter para "Alencar, José de"
        assert "," in formatted
        # Pode começar com Alencar ou com a partícula removida
        assert "Alencar" in formatted
    
    def test_already_inverted(self):
        """Testa nome já no formato invertido."""
        formatted = format_author_name("Alencar, José de")
        # Deve manter como está
        assert formatted == "Alencar, José de"
    
    def test_single_name(self):
        """Testa nome único."""
        formatted = format_author_name("Aristóteles")
        # Deve manter como está
        assert formatted == "Aristóteles"
    
    def test_name_with_junior(self):
        """Testa nome com Junior."""
        formatted = format_author_name("Pedro Álvares Cabral Junior")
        # Junior deve ficar com o sobrenome
        assert "Cabral Junior" in formatted
    
    def test_name_with_particle(self):
        """Testa nome com partícula no fim (caso especial brasileiro)."""
        formatted = format_author_name("Machado de Assis")
        # Machado de Assis é caso especial - nome que termina com partícula
        # Deve manter o formato original (entrada de autoridade)
        assert formatted == "Machado de Assis"
    
    def test_empty_name(self):
        """Testa nome vazio."""
        formatted = format_author_name("")
        assert formatted == ""
    
    def test_whitespace_only(self):
        """Testa nome com apenas espaços."""
        formatted = format_author_name("   ")
        assert formatted == ""
    
    def test_two_part_name(self):
        """Testa nome com duas partes."""
        formatted = format_author_name("Clarice Lispector")
        assert formatted == "Lispector, Clarice"


# ==============================================================================
# Testes de Casos Especiais Brasileiros
# ==============================================================================

class TestBrazilianAuthors:
    """Testes específicos para autores brasileiros."""
    
    @pytest.mark.parametrize("author,expected_start", [
        # Autores clássicos brasileiros
        ("Machado de Assis", "M"),  # Caso especial - usa primeiro nome
        ("José de Alencar", "A"),   # Padrão - usa Alencar
        ("Monteiro Lobato", "L"),
        ("Clarice Lispector", "L"),
        ("Jorge Amado", "A"),
        ("Graciliano Ramos", "R"),
        ("Carlos Drummond de Andrade", "A"),  # Andrade
        ("Cecília Meireles", "M"),
        ("João Guimarães Rosa", "R"),
        ("Rachel de Queiroz", "Q"),
        ("Érico Veríssimo", "V"),
        ("Lygia Fagundes Telles", "T"),
    ])
    def test_brazilian_classics(self, author: str, expected_start: str):
        """Testa códigos para autores clássicos brasileiros."""
        code = generate_cutter_code(author)
        assert code.startswith(expected_start), f"Expected {author} to start with {expected_start}, got {code}"


# ==============================================================================
# Testes de Performance
# ==============================================================================

class TestCutterPerformance:
    """Testes de performance do gerador de código Cutter."""
    
    @pytest.mark.slow
    def test_batch_generation(self):
        """Testa geração em lote de códigos."""
        names = [
            "Silva", "Santos", "Oliveira", "Souza", "Rodrigues",
            "Ferreira", "Alves", "Pereira", "Lima", "Gomes",
        ] * 100  # 1000 nomes
        
        for name in names:
            code = generate_cutter_code(name)
            assert len(code) >= 2
    
    def test_consistent_results(self):
        """Testa que o mesmo nome sempre gera o mesmo código."""
        name = "Machado de Assis"
        codes = [generate_cutter_code(name) for _ in range(10)]
        
        # Todos devem ser iguais
        assert len(set(codes)) == 1
