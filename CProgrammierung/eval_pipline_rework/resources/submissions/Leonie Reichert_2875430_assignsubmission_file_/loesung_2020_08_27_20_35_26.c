#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>

/* DECLARATION */
int readNextLine(void);
int findcolumn(int);
void createcolumn(int, int);
void addstone(int, int);
unsigned char performFullCheck(int, int);
unsigned char prepareNextChecks(void);
unsigned char checkForDeletion(int, int, unsigned char*);
void markForDeletion(int, int);
void deleteMarked(void);
void printResult(void);
void error(int);
void releaseAllAllocated(void);


typedef struct{			// Struktur für die Steine
	unsigned char colour;
	unsigned char toDelete;
} stones;

typedef struct {		// Struktur für eine ganze Spalte
	int columnNo;
	int columnSize;
	int columnInUse;
	stones stonearray[5];	// Es wird zunächst nur von 5 Steinen in einer Spalte ausgegangen. Bei Bedarf kann dieses Array (und damit die ganze Struct) vergrößert werden
} column;


/* GLOBAL VARIABLES */
column** board;				// Array, welches Pointer zu column-structs enthält
int BoardSize = 0;			// Derzeit allozierte Größe des Board-Arrays (in Anzahl an Einträgen)
int BoardInUse = 0;			// Dezeit genutze Größe des Board-Arrays (in Anzahl an Einträgen)
unsigned char available = 0; // Variable die angibt, ob die Spalte für einen Stein schon kreiert wurde
int* deleteArray;			// Array, in das alle zu löschenden Steine eingetragen werden (Enthält x- und y-Koordinate)
int deleteSize = 0;			// Anzahl an Einträgen, die im deleteArray gespeichert werden können * 2
int deleteInUse = 0;		// Anzahl der ints im deleteArray
int lcheckRange = 0;		// Variable die den minimalen Spaltenindex angibt, bei dem bei Folgechecks gecheckt werden muss
int rcheckRange = 0;		// Variable die den maximalen Spaltenindex angibt, bei dem bei Folgechecks gecheckt werden muss
int dcheckRange = 0;		// Variable die den minimalen Höhenindex angibt, bei dem bei Folgechecks gecheckt werden muss. Nicht die tatsächliche y-Koordinate. Subtrahieren von 1 erforderlich



/* DEFINITION */
int main(void)
{	
	// Board-Array wird erstellt für zunächst 5 Spalten
	board = malloc(5 * sizeof(column*));
	
	// Falls Malloc fehlschlägt:
	if(board == NULL)
	{
		error(0);
	}
	BoardSize = 5;
	
	
	// Lösch-Array wird erstellt für zunächst 5 Einträge
	deleteArray = malloc(5 * 2 * sizeof(int));
	
	// Falls Malloc fehlschlägt:
	if(deleteArray == NULL)
	{
		error(0);
	}
	deleteSize = 10;
	
	
	// Das Programm läuft so lange, wie es Eingaben gibt
	// Sobald es keine Eingaben mehr gibt (und alle Löschungen vollzogen sind), können keine weiteren Änderungen im Spielfeld auftreten
	// und das fertige Brett wird ausgegeben
	while(feof(stdin) == 0)
	{
		
		// Funktion, die die nächste Zeile einliest
		// columnindex ist der Index der Spalte im Array des neuen Steins
		int columnindex = readNextLine();
		
		//printf("Stone recognized: %d , %d \n", board[columnindex]->stonearray[board[columnindex]->columnInUse - 1].colour, board[columnindex]->columnNo);		// DEBUG
		
		// columnindex ist -1 wenn eine leere Zeile am Ende der Datei gelesen wurde. Diese wird ignoriert
		if(columnindex == -1)
		{
			// Die Schleife wird neu gestartet. while-Bedingung schlägt fehl und das verbleibende Spielfeld wird ausgegeben
			continue;
		}
		
		// Werte, die angeben, wie weit bei folgenden Checks nach rechts und links geguckt werden muss
		lcheckRange = columnindex;
		rcheckRange = columnindex;
		dcheckRange = board[columnindex]->columnInUse;
		
		// performFirstCheck: Function die überprüft ob es wegen dem neuen Stein neue Löschungen gibt
		// changesMade: Variable die anzeigt, ob es in dieser Runde Löschungen gab. 1 = Ja, 0 = Nein
		unsigned char changesMade = performFullCheck(columnindex, board[columnindex]->columnInUse);
		
		
		
		// Solange es Löschungen gibt, wird nach neuen Löschungen geguckt, die aus den vorherigen entstanden sind.
		while(changesMade)
		{
			// Markierte Steine werden zur Löschung freigegeben
			deleteMarked();
			
			// Es wird nach neuen Reihen gecheckt
			changesMade = prepareNextChecks();	
		}
	}
	
	// Gibt das fertige Spielbrett aus
	printResult();	
	
	return 0;
}



//////////////////////////////////////////////////////////////////////
//////////////////////// ADDING //////////////////////////////////////
//////////////////////////////////////////////////////////////////////



// Funktion, die die nächste Zeile (bzw. den nächsten Stein) einliest
int readNextLine(void)
{
	
	// Einlesen mittels fgetc (Character after Character)
	int newcolumn = 0, newcolour = 0;										// Neue Werte für den nächsten Stein
	unsigned char columnread = 0, colourread = 0, columnnegative = 0;		// Tracking, ob eine Spalte und eine Farbe eingelesen wurde. Trackt außerdem, ob die Spalte negativ ist (0: Nein, 1: Ja)
	
	
	// START
	char next;
	// PHASE 1 (Farbe)
	while(1)
	{
		next = fgetc(stdin);		// Nächster Character wird eingelesen
		
		if(isdigit(next))			// Wenn next eine Ziffer ist, dann gehört es zur Farbe des Steins
		{
			newcolour = newcolour * 10 + (next - '0');
			colourread = 1;
			
			if(newcolour > 254)		// Sollte die Farbe größer als 254 sein, so wird ein Fehler ausgegeben
			{
				error(3);
			}
		}
		else if(next == ' ')		// Ein Leerzeichen deutet das Ende der Farbe an
		{
			break;
		}
		else						// Andere Zeichen als Ziffern und Leerzeichen werden nicht akzeptiert und es wird ggf. ein Fehler ausgegeben
		{
			if(feof(stdin) != 0 && colourread == 0)	// Falls Ende des Input-Streams wird und noch kein Zeichen auf dieser Zeile eingelesen wurde, wird zum Ende der Funktion gesprungen und -1 zurückgegeben
			{
				goto FINAL_EMPTY;
			}
			else					// Andernfalls wird ein Fehler ausgegeben
			{
				error(2);
			}
		}
	}
	
	// PHASE 2 (Zwischenzeichen)
	next = fgetc(stdin);			// Nächstes Zeichen wird eingelesen. Bis hier gab es bereits Farbe + 1 Leerzeichen
	
	while(next == ' ')				// Zusätzliche Leerzeichen werden ignoriert
	{
		next = fgetc(stdin);
	}
	
	if(next == '-')					// Wenn ein Leerzeichen eingelesen wird, dann ist die Spalte negativ
	{
		columnnegative = 1;
		next = fgetc(stdin);
	}
	
	// PHASE 3 (Spalte)
	while(1)						// Einlesen der Spalte
	{
		if(isdigit(next))			// Falls eine Ziffer eingelesen wird, so gehört sie zur Spalte
		{
			newcolumn = newcolumn * 10 + (next - '0');
			columnread = 1;
			
			if(newcolumn > 1048576)
			{
				error(4);
			}
			next = fgetc(stdin);
		}
		else if(next == '\n')		// Sobald ein Newline-Caracter eingelesen wird, ist diese Zeile fertig gelesen
		{
			break;
		}
		else						// Ab hier werden keine anderen Zeichen als Zahlen oder Newline Characters mehr akzeptiert.
		{
			if(feof(stdin) != 0)	// Falls Ende des Input-Streams wird das Programm fortgesetzt
			{
				break;
			}
			else
			{		
				error(2);
			}
		}	
	}
	
	if(colourread == 0 || columnread == 0)	// Sollte keine Spalte oder keine Farbe eingelesen werden, so wird das Programm beendet
	{
		error(5);
	}
	
	if(columnnegative)						// Spaltennummer wird gegebenenfalls negativ gemacht
	{
		newcolumn = newcolumn * (-1);
	}
	
	
	// Finden der Spalte
	int columnindex = findcolumn(newcolumn);
	
	// Sollte die Spalte noch nicht existieren, so wird sie angelegt.
	if(!available)
	{
		// Spalte wird erstellt
		createcolumn(columnindex, newcolumn);
	}
	
	
	// Neuer Stein wird der Spalte hinzugefügt
	addstone(newcolour, columnindex);

	// Spaltenindex des neu eingefügten Steins wird für Reihenchecks zurückgegeben
	return columnindex;
	
	
	// -1 wird zurückgegeben, falls die letzte Zeile in der Datei leer ist (also der letzte Stein mit einem Zeilenumbruch beendet wurde)
	FINAL_EMPTY: return -1;
}



// Funktion, die überprüft, ob die Spalte für den neuen Stein schon angelegt wurde.
// Falls ja, gibt sie den Index der Spalte + 1 zurück (um = 0 abzufangen), falls nein, gibt sie die Position an der sie sein sollte * (-1) - 1 (um = 0 abzufangen) zurück
int findcolumn(int newcolumn)
{
		
	// Finden der Spalte mittels Interpolation Search
	// Es wird angenommen, dass Spalten zumindest in Clustern gleichverteilt vorliegen, da sonst kaum Reihen entstehen könnten
	int min = 0;
	int max = BoardInUse - 1;
	long long pivot = 0;
	
	// Zunächst wird davon ausgegangen, dass die Spalte bereits existiert
	available = 1;
	
	
	// Sonderfall: Es gibt bisher nur 1 Element und gerade wurd das zweite eingelesen => min = max
	if(min == max)
	{
		// Falls die neue Spalte eine größere Spaltennummer hat, als die einzig im Array stehende, so wird sie hinter dieser eingefügt
		if(newcolumn > board[min]->columnNo)
		{
			available = 0;
			return min + 1;
		}
		// Falls die neue Spalte eine kleinere Spaltennummer hat, als die einzig im Array stehende, so wird sie vor dieser eingefügt
		if(newcolumn < board[min]->columnNo)
		{
			available = 0;
			return min;
		}
		// Andernfalls wird weiter im Algorithmus verfahren
	}

	
	// Index wird mittels modifizierter Interpolation Search ermittelt.
	while(min < max)
	{
		
		// Falls die neue Spalte eine höhere Spaltennummer hat, als die max-Spalte, so wird die neue Spalte hinter die max-Spalte gehängt
		if(newcolumn > board[max]->columnNo)
		{
			available = 0;
			return max + 1;
		}
		// Falls die neue Spalte eine kleinere Spaltennummer hat, als die min-Spalte, so wird die neue Spalte vor der min-Spalte gehängt
		if(newcolumn < board[min]->columnNo)
		{
			available = 0;
			return min;
		}
	
		// Berechnung des Pivot-Elementes
		pivot = min + ((long long)(newcolumn - board[min]->columnNo) * (long long)(max - min) / (long long)(board[max]->columnNo - board[min]->columnNo));
		
				
		// Checks
		if(board[pivot]->columnNo < newcolumn)
		{
			min = pivot + 1;
		}
		else if(board[pivot]->columnNo > newcolumn)
		{
			max = pivot;
		}
		else
		{
			return pivot;
		}
	}
	
	// min = max
	if(BoardInUse > 0)
	{
		// Es muss mindestens ein Board-Element geben, um auf board[min].columnNo zuzugreifen
		if(newcolumn == board[min]->columnNo)
		{

			return min;
		}
	}	
	
	// Spalte wurde nicht gefunden
	available = 0;
	return min;
}



// Sollte die Spalte für einen Stein noch nicht existieren, so wird sie hier angelegt.
// Der Index an dem die Spalte kreiert werden soll wird übergeben
void createcolumn(int columnindex, int newcolumn)
{
	
	// Sollte das Board voll sein, so muss mehr Speicher alloziert werden
	if(BoardInUse == BoardSize)
	{
		// Board-Array wird vergrößert (verdoppelt)
		board = realloc(board, BoardSize * 2 * 8);
			
		// Falls Realloc fehlschlägt:
		if(board == NULL)
		{
			error(0);
		}
		BoardSize = BoardSize * 2;
	}
	
	// Memory muss nur verschoben werden, wenn auf dem Speicherplatz der neuen Spalte schon etwas steht
	if(BoardInUse > columnindex)
	{
		// board[columnindex] wird freigemacht indem alle Folgeelemente einen Platz nach hinten verschoben werden (mittels memmove)
		memmove(board + columnindex + 1, board + columnindex, (BoardInUse - columnindex) * 8);
	}

	// Spalten-Structure wird kreiert
	column *thiscolumn = calloc(1, sizeof(column));
	
	// Falls Calloc fehlschlägt
	if(thiscolumn == NULL)
	{
		error(1);
	}
	
	// Setzen der Ausgangswerte. Die Werte der Steine müssen nicht gesetzt werden, da nicht vorhandene Steine nie Beachtung finden (da .columnInUse existiert)
	thiscolumn->columnNo = newcolumn;
	thiscolumn->columnSize = 5;
	thiscolumn->columnInUse = 0;
	
	//Pointer auf Structure wird dem Board-Array hinzugefügt
	board[columnindex] = thiscolumn;
	
	// Anzahl der aktiven Spalten wird um 1 erhöht
	BoardInUse++;
	
}



// Der neue Stein wird zur Spalte hinzugefügt. Gegebenenfalls muss die Spalte vergrößert werden
void addstone(int colour, int columnindex)
{
	
	// Sollte die Spalte bereits voll sein, so muss sie zunächst erweitert werden (Verdopplung)
	if(board[columnindex]->columnInUse == board[columnindex]->columnSize)
	{
		int size = board[columnindex]->columnSize;
		
		// Speicher wird realloziert (Verdoppelt)
		board[columnindex] = realloc(board[columnindex], 12 + (2 * size * 2));
		
		// Falls Realloc fehlschlägt
		if(board[columnindex] == NULL)
		{
			error(1);
		}
		
		// .columnSize Variable wird angepasst
		board[columnindex]->columnSize = size * 2;
		
	}
	
	// Stein wird eingefügt
	int inUse = board[columnindex]->columnInUse;
	
	// Werte des Steins werden gesetzt
	board[columnindex]->stonearray[inUse].colour = colour;
	board[columnindex]->stonearray[inUse].toDelete = 0;
	
	// .columnInUse Variable wird um 1 erhöht
	board[columnindex]->columnInUse = board[columnindex]->columnInUse + 1;
}




//////////////////////////////////////////////////////////////////////
//////////////////////// CHECKS //////////////////////////////////////
//////////////////////////////////////////////////////////////////////



// Function die überprüft ob es wegen eines neuen Steins neue Löschungen gibt
// Dazu erhält die Funktion den Index der zu überprüfenden Spalte, sowie die Höhe des zu prüfenden Steins
// Es wird in alle Richtungen außer nach oben gecheckt.
unsigned char performFullCheck(int columnindex, int thisHeight)
{
	
	// Wert des neu hinzugefügten Steins
	unsigned char value = board[columnindex]->stonearray[thisHeight - 1].colour;
	 
	
	// In diesem Array werden die verschiedenen Reichweiten der Reihen getrackt
	unsigned char rows[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
	
		
	// Methode, mit der nach Reihen geprüft wird (Diese Reihen können erstmal auch kleiner als 4 Steine sein)
	// vert, hori: Vertikaler bzw. Horizonzatler Offset für eine Spalte (z.B. vertikaler Offset bei Diagonalen Checks)
		
	int vert, hori, i;
	
	
	for(hori = -1; hori <= 1; hori++)
	{
		for(vert = -1; vert <= 1; vert++)
		{
			// Die Checks bei hori = 0 werden für vert = {0,1} übersprungen. Es wird nur nach unten gecheckt.
			if(hori == 0 && vert != -1)
			{
				break;
			}
			
			// Es muss für jede mögliche Reihe nur drei Schritte gegangen werden, da bisherige Reihen maximal 3 Steine lang sein können
			for(i = 1; i <= 3; i++)
			{
				// Die Spalte muss existieren
				if(columnindex + hori * i >= 0 && columnindex + hori * i <= BoardInUse - 1)
				{
					// Die zu prüfende Spalte muss nahtlos anliegen (D.h. es darf keine Lücke in den Zeilnnummern geben
					// Außerdem muss die zu prüfende Spalte genug Höhe haben
					// Zuletzt darf unser Zugriff nicht zu weit unten stattfinden.
					if(board[columnindex + hori * i]->columnNo == board[columnindex]->columnNo + hori * i && board[columnindex + hori * i]->columnInUse >= thisHeight + vert * i && thisHeight + vert * i > 0)
					{
						// Falls die Farben des neuen Steins und des zu überprüfenden Steins übereinstimmen
						if(board[columnindex + hori * i]->stonearray[(thisHeight - 1) + vert * i].colour == value)
						{
							// Counter für diese Reihe wird um 1 erhöht.
							rows[(hori + 1) * 3 + (vert + 1)] = rows[(hori + 1) * 3 + (vert + 1)] + 1;
						}
						else
						{

							break;
						}
					}
					// Anonsten können mögliche weitere Checks für diese Reihe übersprungen werden, da es entweder die anliegende Reihe nich gibt, diese nicht hoch genug ist, oder wir zu weit unten sind für die Checks
					else
					{

						break;
					}
				}
				// Wenn die Spalte nicht existiert, werden auch die folgenden Spalten nicht existieren. Wir können hier abbrechen
				else
				{
						
					break;
				}		
			}
			
		}
		
	}
	
	// Es wird nach Löschungen mittels des Rows-Arrays überprüft
	// changesMade: Trackt, ob irgendwelche Steine gelöscht worden sind
	unsigned char changesMade = checkForDeletion(columnindex, thisHeight, rows);
	
	return changesMade;
}




// Funktion die die Checks für alle benötigten Steine  koordiniert
unsigned char prepareNextChecks()
{	
	// Die Ranges werden gespeichert
	int lthisRange = lcheckRange;
	int rthisRange = rcheckRange;
	int dthisRange = dcheckRange;
	
	// Defaults für die neuen Ranges werden gesetzt
	lcheckRange = rthisRange;
	rcheckRange = lthisRange;
	dcheckRange = 2147483647;		// Wird auf den maximalen Int-Wert gesetzt
	
	
	// changesMade für alle Felder
	// Sollte bei eirgendeinem Stein eine Löschung vorgenommen worden sein, so ist diese Variable 1;
	unsigned char totalChangesMade = 0;
	
	// Für jeden Stein innerhalb der Box wird ein Full-Check gemacht
	int i, j;
	for(i = lthisRange; i <= rthisRange; i++)
	{
		// Jede Spalte wird von oben angefangen
		for(j = dthisRange; j <= board[i]->columnInUse; j++)
		{
			unsigned char thisChangesMade = performFullCheck(i,j);
			
			// Sollte bei diesem Vorgang eine Änderung aufgetreten sein, so wird die totalChangesMade-Variable auf 1 gesetzt
			if(thisChangesMade)
			{
				totalChangesMade = 1;
			}
		}
	}
	
	return totalChangesMade;
}


//////////////////////////////////////////////////////////////////////
//////////////////////// DELETION ////////////////////////////////////
//////////////////////////////////////////////////////////////////////



// Funktion, welche überprüft, ob Steine gelöscht werden müssen und löschpflichtige Steine zu einer weiteren Löschfunktion weiterleitet
unsigned char checkForDeletion(int columnindex, int thisHeight, unsigned char rows[])
{	
	
	// changesMade: Trackt, ob irgendwelche Steine gelöscht worden sind
	unsigned char changesMade = 0;
	
	// Formel für rows-Array ist: rows[(hori + 1) * 3 + (vert + 1)]
	 
	// Checks werden durchgeführt:
	int i, j, rowCount;
	for(i = 0; i <= 2; i++)
	{
		// Es wird immer die Summe gegenüberliegender Linien genommen (Stein kann ja in der Mitte einer Reihen liegen)
		// Der Stein selber zählt ebenfalls zur Reihe dazu
		rowCount = rows[i] + rows[8-i] + 1;
		
		// Sollte RowCount >= 4 sein, so liegt eine löschpflichtige Reihe vor
		if(rowCount >= 4)
		{
			changesMade = 1;
			
			// lcheckRange, rcheckRange und dcheckRange werden für möglicherweise folgende Checks erhöht
			if(columnindex - rows[i] < lcheckRange)
			{
				lcheckRange = columnindex - rows[i];
			}
			if(columnindex + rows[8-i] > rcheckRange)
			{
				rcheckRange = columnindex + rows[8-i];
			}
			
			// dcheckRange soll nur für nach unten zeigende Linien geupdated werden
			// Nach unten zeigende Linien sind rows[0] und rows[6]
			// Diagonalen
			if((i == 0 || i == 2) && thisHeight + -1 * rows[i*3] < dcheckRange)
			{
				dcheckRange = thisHeight + -1 * rows[i*3];
			}
			// Horizontalen
			if(i == 1 && thisHeight < dcheckRange)
			{
				dcheckRange = thisHeight;
			}
			
			
			
			// Steine links vom neuen Stein werden zum Löschen freigegeben
			for(j = 1; j <= rows[i]; j++)
			{
				// Löschkoordinaten werden errechnet
				// Wichtig: int thisHeight ist nicht der Index im Array. Dafür muss noch 1 abgezogen werden
				
				markForDeletion(columnindex - j, thisHeight + j * (i - 1));
			}
			
			// Steine rechts vom neuen Stein werden zum Löschen freigegeben
			for(j = 1; j <= rows[8-i]; j++)
			{
				// Löschkoordinaten werden errechnet
				// Wichtig: int thisHeight ist nicht der Index im Array. Dafür muss noch 1 abgezogen werden
				// Bei den rechten Löschungen, ist der y-Offset invertiert im Vergleich zu den rechten Löschungen. Linien müssen sich immer gegenüber liegen

				markForDeletion(columnindex + j, thisHeight + j * (i - 1) * -1);
			}
			
			// Hauptstein wird zur Löschung freigegeben			
			markForDeletion(columnindex, thisHeight);
		}
	}
	
	// Spezialcheck nach unten
	{
		// Falls die drei Steine unter dem betrachteten Stein die gleiche Farbe haben, so ist eine 4er-Reihe entstanden
		if(rows[3] >= 3)
		{
			changesMade = 1;
			
			// dcheckRange wird ggf. angepasst
			if(thisHeight - rows[3] < dcheckRange)
			{
				dcheckRange = thisHeight - rows[3];
			}
			
			// rcheckRange wird ggf. angepasst
			if(columnindex > rcheckRange)
			{
				rcheckRange = columnindex;
			}
			
			// lcheckRange wird ggf. angepasst
			if(columnindex < lcheckRange)
			{
				lcheckRange = columnindex;
			}
			
			// Steine werden zum Löschen freigegeben (inklusive Hauptstein)
			int i;
			for(i = 0; i <= rows[3]; i++)
			{
				
				markForDeletion(columnindex, thisHeight - i);
			}
			
		}
	}
	
	// changesMade wird zurückgegeben
	return changesMade;
}




// Funktion, die löschpflichtige Steine markiert und diese zum Lösch-Array hinzufügt
void markForDeletion(int columnindex, int thisHeight)
{
	
	// Es wird geprüft, ob der Stein bereits zum Löschen vorgemerkt wurde
	if(board[columnindex]->stonearray[thisHeight - 1].toDelete == 1)
	{	
		// Falls ja, muss hier nichts weiter geschehen
		return;
	}
	
	// Falls nein, muss der Stein zum Löschen markiert werden und in das Lösch-Array eingetragen werden
	
	// Stein wid zum Löschen markeiert
	board[columnindex]->stonearray[thisHeight - 1].toDelete = 1;
	
	// Stein wird in das Lösch-Array eingetragen
	// Sollte das Lösch-Array zu klein sein, so muss es zunächst vergrößert werden
	if(deleteSize == deleteInUse)
	{
		deleteArray = realloc(deleteArray, sizeof(int) * deleteSize * 2);
		deleteSize = deleteSize * 2;
		
		// Falls Realloc fehlschlägt
		if(deleteArray == NULL)
		{
			error(0);
		}
	}
	
	// Stein wird dem Lösch-Array hinzugefügt
	// x-Koordinate
	deleteArray[deleteInUse] = columnindex;
	// y-Koordinate
	deleteArray[deleteInUse + 1] = thisHeight;
	
	// deleteInUse wird erhöht
	deleteInUse = deleteInUse + 2;
	
}





// Funktion, die alle markierten Steine löscht
void deleteMarked(void)
{
	
	int i;
	for(i = 0; i < deleteInUse; i = i + 2)
	{
		
		// x- und y-Koordinate des zu löschenden Steins werden beschafft
		int column = deleteArray[i];
		int height = deleteArray[i + 1] - 1;
		
		
		// Da der zu löschende Stein durch vorherige Löschungen schon nach unten verschieben sein könnte, muss er nochmal gesucht werden. Ausgangspunkt sind die gegebenen Koordinaten
		while(1)
		{
			// Wir können ab hier die Steine überprüfen
			if(height < board[column]->columnInUse)
			{
				// Suche nach dem Stein mittels der .toDelete Flags
				while(1)
				{
					// Der Stein wurde gefunden
					if(board[column]->stonearray[height].toDelete == 1)
					{							
										
						// Der Stein liegt NICHT ganz oben
						if(height < board[column]->columnInUse - 1)
						{
							// Der Stein wird überschrieben
							memmove(&(board[column]->stonearray[height].colour), &(board[column]->stonearray[height + 1].colour), (board[column]->columnInUse - 1 - height) * sizeof(stones));					
						}
						
						// .columnInUse wird um 1 verringert
						board[column]->columnInUse = board[column]->columnInUse - 1;
									
						break;
						
					}
					
					// Der Stein wurde nicht gefunden
					height--;
					
					if(height < 0)
					{
						error(6);
					}
				}
			}
			else
			{
				// Die Spalte hat sich verkleinert und es gibt hier keine Steine auf die wir zugreifen könnten
				height--;
				
				if(height < 0)
				{
					error(6);
				}
				
				continue;
			}
			
			break;
		}

	}
	
	
	// deleteInUse wird zurückgesetzt
	deleteInUse = 0;
}



//////////////////////////////////////////////////////////////////////
////////////////////// END OF PROGRAM ////////////////////////////////
//////////////////////////////////////////////////////////////////////



// Finale Ausgabefunktion
void printResult(void)
{
	int i,j;
	for(i = 0; i < BoardInUse; i++)
	{
		for(j = 0; j < board[i]->columnInUse; j++)
		{
			fprintf(stdout, "%d %d %d\n", board[i]->stonearray[j].colour, board[i]->columnNo, j);
		}
	}
	
	releaseAllAllocated();
}



void error(int type)
{
	// Freigeben allen allozierten Speichers
	releaseAllAllocated();
		
	
	// Fehlermeldungen
	if(type == 0)
	{
		fprintf(stderr, "Error | Unable to allocate sufficient memory for required Arrays. Program will terminate. \n");
	}
	if(type == 1)
	{
		fprintf(stderr, "Error | Unable to allocate sufficient memory for required Structure. Program will terminate. \n");
	}
	else if(type == 2)
	{
		fprintf(stderr, "Error | Input does not meet accepted criteria. Program will terminate. \n");
	}
	else if(type == 3)
	{
		fprintf(stderr, "Error | Value 'Colour' for an element is outside specified parameters. Program will terminate. \n");
	}
	else if(type == 4)
	{
		fprintf(stderr, "Error | Value 'Column' for an element is outside specified parameters. Program will terminate. \n");
	}
	else if(type == 5)
	{
		fprintf(stderr, "Error | Values for an element are incomplete or do not exist at all. Program will terminate. \n");
	}
	else if(type == 6)
	{
		fprintf(stderr, "Error | Unable to locate an element for deletion. Program will terminate. \n");
	}
	
	
	else
	{
		fprintf(stderr, "Error | An unknown error occured. Program will terminate. \n");
	}
	
	// Programmabbruch
	exit(1);
}


// Funktion, die jeglichen allozierten Speicher wieder freigibt
void releaseAllAllocated(void)
{
	// Spalten werden freigegeben
	int i;
	for(i = 0; i < BoardInUse; i++)
	{
		free(board[i]);
	}
	
	// Board-Array wird freigegeben
	free(board);
	
	// deleteArray wird freigegeben
	free(deleteArray);	
}
