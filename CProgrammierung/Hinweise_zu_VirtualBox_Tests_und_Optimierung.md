
# Anleitung zur Verwendung des VirtualBox images (Für MS Windows Nutzer)

* Installieren Sie VirtualBox.
* Starten Sie VirtualBox.
* Speichern Sie die von uns zur Verfügung gestellte Appliance auf ihrer Festplatte.
* Importieren Sie die Appliance
    * [File]->[Import Appliance...]
    * .ova Datei auswählen
	* alle Einstellungen können übernommen werden.
* Legen Sie einen "shared folder" fest
    * [Machine]->[Settings] --> [Shared Folders]
    * Add Folder
	    * [Folder Path] = `C:\Pfad\zu\Ihrer\Loesung`
	    * [Folder Name] = `share`
		* [Auto mount] = true
		* [OK]
* Starten Sie die virtuelle Maschine.
* Im Konsolenfenster loggen Sie sich ein. User: ds, Password: ds
* Führen Sie nun folgende Kommandos aus:
```
cd /media/sf_share
gcc -std=c11 -Werror -Wall -O3 -o loesung loesung-*.c
```

# Tipps zum Testen

* Erlegen Sie ihrem Programm ein Heap Limit auf (z.B. 500MB):
```
ulimit -d 500000
```

* Testen Sie die Korrektheit der von Ihrem Programm generierten Ausgabe z.B. mit
```
./loesung < graph5.in | sort -n | diff -q -- - graph5.out
```

* Vergessen Sie nicht, auch zu testen, ob Ihr Programm bei falschen Eingabedaten
    * eine Fehlermeldung ausgibt
    * Allen vom Heap allozierten Speicher wieder frei gibt (z.B. valgrind verwenden)
	* es nicht zu segfaults kommt.

* Sinnvolle Testfälle für falsche Eingaben wären zum Beispiel:
    * die leere Eingabe
    * /dev/urandom
	* an sich korrekte Eingaben, die aber zu große oder negative Zahlen enthalten
	* Eingaben, die Zeilen mit 0,2,4 oder mehr Zahlen enthalten.
	* Eingaben, die eine falsch formatierte erste Zeile enthalten
	* Eingaben, die gar kein linefeed enthalten

* Testen Sie ihr Programm auch mit sehr geringem Heap limit
(ulimit -d) oder cpu time limit (ulimit -t). Zwar können Sie dann nicht mehr
erwarten, eine korrekte Ausgabe zu erhalten. Segfaults sollten trotzdem niemals
auftrefen.

# Weitere Hinweise

* Ihr Programm soll im Prinzip mit beliebigen in der Aufgabenstellung
    beschriebenen Eingabedaten umgehen können, sofern genügend
    Speicher und Laufzeit zur Verfügung stehen.

    Zu Zwecken der Optimierung dürfen Sie aber davon ausgehen, dass
    wir für die Überprüfung, ob Ihr Programm eine korrekte Ausgabe
    erzeugt, nur solche Eingaben verwenden, deren Graphen problemlos
    in 1GB Hauptspeicher abgebildet werden können und bei denen die
    deutliche Mehrheit der Knoten mindestens eine einlaufende oder
    auslaufende Kante hat.

    Beachten Sie aber, dass bei unzureichendem Speicher kein segfault
    auftritt, sondern das Programm mit einer passenden Fehlermeldung
    selbst abbricht.

    * Beispiel:
	
        Bei einer Eingabe wie
```
0 3000000000 1
0 1000000000 1
1000000000 3000000000 1
1000000000
```
        darf ihr Programm mit einem Verweis auf zu wenig verfügbaren
        Speicher abbrechen, auch wenn `1000000000` die korrekte Ausgabe
        ist.


