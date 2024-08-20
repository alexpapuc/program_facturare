# Aplicatie facturare
Aplicatia citeste de la tastatura informatii despre:
- Furnizor
- Clienti
- Produse
- Facturi

Informatiile sunt stocate intr-o baza de date.
Prin intermediul aplicatiei se pot efectua operatii de: adaugare, stergere, afisare - furnizor, 
clienti, produse, facturi si emitere facturi.
Facturile emise se vor salva in folderul proiectului sub forma de fisier word.

Instalare
cloneaza repozitory-ul
navigheaza in folderul proiectului creaza un virtual environment si instaleaza dependintele
Utilizare
deschide un terminal de comanda
activeaza virtual environment-ul creat la pasul anterior
cu virtual environment activat introdu comanda: py p_facturare.py si opereaza in meniul interactiv.

# Instalare

Proiectul ruleaza pe versiuni de Python 3.10 sau mai mari.

Proiectul contine dependinte cum ar fi: SQLAlchemy, MailMerge, mysqlclient, de aceea
trebuie sa le instalam separat, folosind comanda:

```pip install -r requirements.txt```

# Utilizare

```python p_facturare.py```

Va genera un meniu interactiv, de unde iti vei putea alege optiunile:

```
Introdu cifra corespunzatoare operatiunii dorite:
    1 Afisare furnizori, clienti, produse, facturi;
    2 Adaugare furnizori, clienti, produse, Emitere facturi;
    3 Stergere furnizori, clienti, produse, facturi
    0 Exit
```