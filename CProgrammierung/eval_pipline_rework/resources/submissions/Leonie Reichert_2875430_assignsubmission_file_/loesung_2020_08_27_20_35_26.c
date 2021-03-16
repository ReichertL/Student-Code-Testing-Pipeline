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


typedef struct{			// Struktur f�r die Steine
	unsigned char colour;
	unsigned char toDelete;
} stones;

typedef struct {		// Struktur f�r eine ganze Spalte
	int columnNo;
	int columnSize;
	int columnInUse;
	stones stonearray[5];	// Es wird zun�chst nur von 5 Steinen in einer Spalte ausgegangen. Bei Bedarf kann dieses Array (und damit die ganze Struct) vergr��ert werden
} column;


/* GLOBAL VARIABLES */
column** board;				// Array, welches Pointer zu column-structs enth�lt
int BoardSize = 0;			// Derzeit allozierte Gr��e des Board-Arrays (in Anzahl an Eintr�gen)
int BoardInUse = 0;			// Dezeit genutze Gr��e des Board-Arrays (in Anzahl an Eintr�gen)
unsigned char available = 0; // Variable die angibt, ob die Spalte f�r einen Stein schon kreiert wurde
int* deleteArray;			// Array, in das alle zu l�schenden Steine eingetragen werden (Enth�lt x- und y-Koordinate)
int deleteSize = 0;			// Anzahl an Eintr�gen, die im deleteArray gespeichert werden k�nnen * 2
int deleteInUse = 0;		// Anzahl der ints im deleteArray
int lcheckRange = 0;		// Variable die den minimalen Spaltenindex angibt, bei dem bei Folgechecks gecheckt werden muss
int rcheckRange = 0;		// Variable die den maximalen Spaltenindex angibt, bei dem bei Folgechecks gecheckt werden muss
int dcheckRange = 0;		// Variable die den minimalen H�henindex angibt, bei dem bei Folgechecks gecheckt werden muss. Nicht die tats�chliche y-Koordinate. Subtrahieren von 1 erforderlich



/* DEFINITION */
int main(void)
{	
	// Board-Array wird erstellt f�r zun�chst 5 Spalten
	board = malloc(5 * sizeof(column*));
	
	// Falls Malloc fehlschl�gt:
	if(board == NULL)
	{
		error(0);
	}
	BoardSize = 5;
	
	
	// L�sch-Array wird erstellt f�r zun�chst 5 Eintr�ge
	deleteArray = malloc(5 * 2 * sizeof(int));
	
	// Falls Malloc fehlschl�gt:
	if(deleteArray == NULL)
	{
		error(0);
	}
	deleteSize = 10;
	
	
	// Das Programm l�uft so lange, wie es Eingaben gibt
	// Sobald es keine Eingaben mehr gibt (und alle L�schungen vollzogen sind), k�nnen keine weiteren �nderungen im Spielfeld auftreten
	// und das fertige Brett wird ausgegeben
	while(feof(stdin) == 0)
	{
		
		// Funktion, die die n�chste Zeile einliest
		// columnindex ist der Index der Spalte im Array des neuen Steins
		int columnindex = readNextLine();
		
		//printf("Stone recognized: %d , %d \n", board[columnindex]->stonearray[board[columnindex]->columnInUse - 1].colour, board[columnindex]->columnNo);		// DEBUG
		
		// columnindex ist -1 wenn eine leere Zeile am Ende der Datei gelesen wurde. Diese wird ignoriert
		if(columnindex == -1)
		{
			// Die Schleife wird neu gestartet. while-Bedingung schl�gt fehl und das verbleibende Spielfeld wird ausgegeben
			continue;
		}
		
		// Werte, die angeben, wie weit bei folgenden Checks nach rechts und links geguckt werden muss
		lcheckRange = columnindex;
		rcheckRange = columnindex;
		dcheckRange = board[columnindex]->columnInUse;
		
		// performFirstCheck: Function die �berpr�ft ob es wegen dem neuen Stein neue L�schungen gibt
		// changesMade: Variable die anzeigt, ob es in dieser Runde L�schungen gab. 1 = Ja, 0 = Nein
		unsigned char changesMade = performFullCheck(columnindex, board[columnindex]->columnInUse);
		
		
		
		// Solange es L�schungen gibt, wird nach neuen L�schungen geguckt, die aus den vorherigen entstanden sind.
		while(changesMade)
		{
			// Markierte Steine werden zur L�schung freigegeben
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



// Funktion, die die n�chste Zeile (bzw. den n�chsten Stein) einliest
int readNextLine(void)
{
	
	// Einlesen mittels fgetc (Character after Character)
	int newcolumn = 0, newcolour = 0;										// Neue Werte f�r den n�chsten Stein
	unsigned char columnread = 0, colourread = 0, columnnegative = 0;		// Tracking, ob eine Spalte und eine Farbe eingelesen wurde. Trackt au�erdem, ob die Spalte negativ ist (0: Nein, 1: Ja)
	
	
	// START
	char next;
	// PHASE 1 (Farbe)
	while(1)
	{
		next = fgetc(stdin);		// N�chster Character wird eingelesen
		
		if(isdigit(next))			// Wenn next eine Ziffer ist, dann geh�rt es zur Farbe des Steins
		{
			newcolour = newcolour * 10 + (next - '0');
			colourread = 1;
			
			if(newcolour > 254)		// Sollte die Farbe gr��er als 254 sein, so wird ein Fehler ausgegeben
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
			if(feof(stdin) != 0 && colourread == 0)	// Falls Ende des Input-Streams wird und noch kein Zeichen auf dieser Zeile eingelesen wurde, wird zum Ende der Funktion gesprungen und -1 zur�ckgegeben
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
	next = fgetc(stdin);			// N�chstes Zeichen wird eingelesen. Bis hier gab es bereits Farbe + 1 Leerzeichen
	
	while(next == ' ')				// Zus�tzliche Leerzeichen werden ignoriert
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
		if(isdigit(next))			// Falls eine Ziffer eingelesen wird, so geh�rt sie zur Spalte
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
	
	
	// Neuer Stein wird der Spalte hinzugef�gt
	addstone(newcolour, columnindex);

	// Spaltenindex des neu eingef�gten Steins wird f�r Reihenchecks zur�ckgegeben
	return columnindex;
	
	
	// -1 wird zur�ckgegeben, falls die letzte Zeile in der Datei leer ist (also der letzte Stein mit einem Zeilenumbruch beendet wurde)
	FINAL_EMPTY: return -1;
}



// Funktion, die �berpr�ft, ob die Spalte f�r den neuen Stein schon angelegt wurde.
// Falls ja, gibt sie den Index der Spalte + 1 zur�ck (um = 0 abzufangen), falls nein, gibt sie die Position an der sie sein sollte * (-1) - 1 (um = 0 abzufangen) zur�ck
int findcolumn(int newcolumn)
{
		
	// Finden der Spalte mittels Interpolation Search
	// Es wird angenommen, dass Spalten zumindest in Clustern gleichverteilt vorliegen, da sonst kaum Reihen entstehen k�nnten
	int min = 0;
	int max = BoardInUse - 1;
	long long pivot = 0;
	
	// Zun�chst wird davon ausgegangen, dass die Spalte bereits existiert
	available = 1;
	
	
	// Sonderfall: Es gibt bisher nur 1 Element und gerade wurd das zweite eingelesen => min = max
	if(min == max)
	{
		// Falls die neue Spalte eine gr��ere Spaltennummer hat, als die einzig im Array stehende, so wird sie hinter dieser eingef�gt
		if(newcolumn > board[min]->columnNo)
		{
			available = 0;
			return min + 1;
		}
		// Falls die neue Spalte eine kleinere Spaltennummer hat, als die einzig im Array stehende, so wird sie vor dieser eingef�gt
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
		
		// Falls die neue Spalte eine h�here Spaltennummer hat, als die max-Spalte, so wird die neue Spalte hinter die max-Spalte geh�ngt
		if(newcolumn > board[max]->columnNo)
		{
			available = 0;
			return max + 1;
		}
		// Falls die neue Spalte eine kleinere Spaltennummer hat, als die min-Spalte, so wird die neue Spalte vor der min-Spalte geh�ngt
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



// Sollte die Spalte f�r einen Stein noch nicht existieren, so wird sie hier angelegt.
// Der Index an dem die Spalte kreiert werden soll wird �bergeben
void createcolumn(int columnindex, int newcolumn)
{
	
	// Sollte das Board voll sein, so muss mehr Speicher alloziert werden
	if(BoardInUse == BoardSize)
	{
		// Board-Array wird vergr��ert (verdoppelt)
		board = realloc(board, BoardSize * 2 * 8);
			
		// Falls Realloc fehlschl�gt:
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
	
	// Falls Calloc fehlschl�gt
	if(thiscolumn == NULL)
	{
		error(1);
	}
	
	// Setzen der Ausgangswerte. Die Werte der Steine m�ssen nicht gesetzt werden, da nicht vorhandene Steine nie Beachtung finden (da .columnInUse existiert)
	thiscolumn->columnNo = newcolumn;
	thiscolumn->columnSize = 5;
	thiscolumn->columnInUse = 0;
	
	//Pointer auf Structure wird dem Board-Array hinzugef�gt
	board[columnindex] = thiscolumn;
	
	// Anzahl der aktiven Spalten wird um 1 erh�ht
	BoardInUse++;
	
}



// Der neue Stein wird zur Spalte hinzugef�gt. Gegebenenfalls muss die Spalte vergr��ert werden
void addstone(int colour, int columnindex)
{
	
	// Sollte die Spalte bereits voll sein, so muss sie zun�chst erweitert werden (Verdopplung)
	if(board[columnindex]->columnInUse == board[columnindex]->columnSize)
	{
		int size = board[columnindex]->columnSize;
		
		// Speicher wird realloziert (Verdoppelt)
		board[columnindex] = realloc(board[columnindex], 12 + (2 * size * 2));
		
		// Falls Realloc fehlschl�gt
		if(board[columnindex] == NULL)
		{
			error(1);
		}
		
		// .columnSize Variable wird angepasst
		board[columnindex]->columnSize = size * 2;
		
	}
	
	// Stein wird eingef�gt
	int inUse = board[columnindex]->columnInUse;
	
	// Werte des Steins werden gesetzt
	board[columnindex]->stonearray[inUse].colour = colour;
	board[columnindex]->stonearray[inUse].toDelete = 0;
	
	// .columnInUse Variable wird um 1 erh�ht
	board[columnindex]->columnInUse = board[columnindex]->columnInUse + 1;
}




//////////////////////////////////////////////////////////////////////
//////////////////////// CHECKS //////////////////////////////////////
//////////////////////////////////////////////////////////////////////



// Function die �berpr�ft ob es wegen eines neuen Steins neue L�schungen gibt
// Dazu erh�lt die Funktion den Index der zu �berpr�fenden Spalte, sowie die H�he des zu pr�fenden Steins
// Es wird in alle Richtungen au�er nach oben gecheckt.
unsigned char performFullCheck(int columnindex, int thisHeight)
{
	
	// Wert des neu hinzugef�gten Steins
	unsigned char value = board[columnindex]->stonearray[thisHeight - 1].colour;
	 
	
	// In diesem Array werden die verschiedenen Reichweiten der Reihen getrackt
	unsigned char rows[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
	
		
	// Methode, mit der nach Reihen gepr�ft wird (Diese Reihen k�nnen erstmal auch kleiner als 4 Steine sein)
	// vert, hori: Vertikaler bzw. Horizonzatler Offset f�r eine Spalte (z.B. vertikaler Offset bei Diagonalen Checks)
		
	int vert, hori, i;
	
	
	for(hori = -1; hori <= 1; hori++)
	{
		for(vert = -1; vert <= 1; vert++)
		{
			// Die Checks bei hori = 0 werden f�r vert = {0,1} �bersprungen. Es wird nur nach unten gecheckt.
			if(hori == 0 && vert != -1)
			{
				break;
			}
			
			// Es muss f�r jede m�gliche Reihe nur drei Schritte gegangen werden, da bisherige Reihen maximal 3 Steine lang sein k�nnen
			for(i = 1; i <= 3; i++)
			{
				// Die Spalte muss existieren
				if(columnindex + hori * i >= 0 && columnindex + hori * i <= BoardInUse - 1)
				{
					// Die zu pr�fende Spalte muss nahtlos anliegen (D.h. es darf keine L�cke in den Zeilnnummern geben
					// Au�erdem muss die zu pr�fende Spalte genug H�he haben
					// Zuletzt darf unser Zugriff nicht zu weit unten stattfinden.
					if(board[columnindex + hori * i]->columnNo == board[columnindex]->columnNo + hori * i && board[columnindex + hori * i]->columnInUse >= thisHeight + vert * i && thisHeight + vert * i > 0)
					{
						// Falls die Farben des neuen Steins und des zu �berpr�fenden Steins �bereinstimmen
						if(board[columnindex + hori * i]->stonearray[(thisHeight - 1) + vert * i].colour == value)
						{
							// Counter f�r diese Reihe wird um 1 erh�ht.
							rows[(hori + 1) * 3 + (vert + 1)] = rows[(hori + 1) * 3 + (vert + 1)] + 1;
						}
						else
						{

							break;
						}
					}
					// Anonsten k�nnen m�gliche weitere Checks f�r diese Reihe �bersprungen werden, da es entweder die anliegende Reihe nich gibt, diese nicht hoch genug ist, oder wir zu weit unten sind f�r die Checks
					else
					{

						break;
					}
				}
				// Wenn die Spalte nicht existiert, werden auch die folgenden Spalten nicht existieren. Wir k�nnen hier abbrechen
				else
				{
						
					break;
				}		
			}
			
		}
		
	}
	
	// Es wird nach L�schungen mittels des Rows-Arrays �berpr�ft
	// changesMade: Trackt, ob irgendwelche Steine gel�scht worden sind
	unsigned char changesMade = checkForDeletion(columnindex, thisHeight, rows);
	
	return changesMade;
}




// Funktion die die Checks f�r alle ben�tigten Steine  koordiniert
unsigned char prepareNextChecks()
{	
	// Die Ranges werden gespeichert
	int lthisRange = lcheckRange;
	int rthisRange = rcheckRange;
	int dthisRange = dcheckRange;
	
	// Defaults f�r die neuen Ranges werden gesetzt
	lcheckRange = rthisRange;
	rcheckRange = lthisRange;
	dcheckRange = 2147483647;		// Wird auf den maximalen Int-Wert gesetzt
	
	
	// changesMade f�r alle Felder
	// Sollte bei eirgendeinem Stein eine L�schung vorgenommen worden sein, so ist diese Variable 1;
	unsigned char totalChangesMade = 0;
	
	// F�r jeden Stein innerhalb der Box wird ein Full-Check gemacht
	int i, j;
	for(i = lthisRange; i <= rthisRange; i++)
	{
		// Jede Spalte wird von oben angefangen
		for(j = dthisRange; j <= board[i]->columnInUse; j++)
		{
			unsigned char thisChangesMade = performFullCheck(i,j);
			
			// Sollte bei diesem Vorgang eine �nderung aufgetreten sein, so wird die totalChangesMade-Variable auf 1 gesetzt
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



// Funktion, welche �berpr�ft, ob Steine gel�scht werden m�ssen und l�schpflichtige Steine zu einer weiteren L�schfunktion weiterleitet
unsigned char checkForDeletion(int columnindex, int thisHeight, unsigned char rows[])
{	
	
	// changesMade: Trackt, ob irgendwelche Steine gel�scht worden sind
	unsigned char changesMade = 0;
	
	// Formel f�r rows-Array ist: rows[(hori + 1) * 3 + (vert + 1)]
	 
	// Checks werden durchgef�hrt:
	int i, j, rowCount;
	for(i = 0; i <= 2; i++)
	{
		// Es wird immer die Summe gegen�berliegender Linien genommen (Stein kann ja in der Mitte einer Reihen liegen)
		// Der Stein selber z�hlt ebenfalls zur Reihe dazu
		rowCount = rows[i] + rows[8-i] + 1;
		
		// Sollte RowCount >= 4 sein, so liegt eine l�schpflichtige Reihe vor
		if(rowCount >= 4)
		{
			changesMade = 1;
			
			// lcheckRange, rcheckRange und dcheckRange werden f�r m�glicherweise folgende Checks erh�ht
			if(columnindex - rows[i] < lcheckRange)
			{
				lcheckRange = columnindex - rows[i];
			}
			if(columnindex + rows[8-i] > rcheckRange)
			{
				rcheckRange = columnindex + rows[8-i];
			}
			
			// dcheckRange soll nur f�r nach unten zeigende Linien geupdated werden
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
			
			
			
			// Steine links vom neuen Stein werden zum L�schen freigegeben
			for(j = 1; j <= rows[i]; j++)
			{
				// L�schkoordinaten werden errechnet
				// Wichtig: int thisHeight ist nicht der Index im Array. Daf�r muss noch 1 abgezogen werden
				
				markForDeletion(columnindex - j, thisHeight + j * (i - 1));
			}
			
			// Steine rechts vom neuen Stein werden zum L�schen freigegeben
			for(j = 1; j <= rows[8-i]; j++)
			{
				// L�schkoordinaten werden errechnet
				// Wichtig: int thisHeight ist nicht der Index im Array. Daf�r muss noch 1 abgezogen werden
				// Bei den rechten L�schungen, ist der y-Offset invertiert im Vergleich zu den rechten L�schungen. Linien m�ssen sich immer gegen�ber liegen

				markForDeletion(columnindex + j, thisHeight + j * (i - 1) * -1);
			}
			
			// Hauptstein wird zur L�schung freigegeben			
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
			
			// Steine werden zum L�schen freigegeben (inklusive Hauptstein)
			int i;
			for(i = 0; i <= rows[3]; i++)
			{
				
				markForDeletion(columnindex, thisHeight - i);
			}
			
		}
	}
	
	// changesMade wird zur�ckgegeben
	return changesMade;
}




// Funktion, die l�schpflichtige Steine markiert und diese zum L�sch-Array hinzuf�gt
void markForDeletion(int columnindex, int thisHeight)
{
	
	// Es wird gepr�ft, ob der Stein bereits zum L�schen vorgemerkt wurde
	if(board[columnindex]->stonearray[thisHeight - 1].toDelete == 1)
	{	
		// Falls ja, muss hier nichts weiter geschehen
		return;
	}
	
	// Falls nein, muss der Stein zum L�schen markiert werden und in das L�sch-Array eingetragen werden
	
	// Stein wid zum L�schen markeiert
	board[columnindex]->stonearray[thisHeight - 1].toDelete = 1;
	
	// Stein wird in das L�sch-Array eingetragen
	// Sollte das L�sch-Array zu klein sein, so muss es zun�chst vergr��ert werden
	if(deleteSize == deleteInUse)
	{
		deleteArray = realloc(deleteArray, sizeof(int) * deleteSize * 2);
		deleteSize = deleteSize * 2;
		
		// Falls Realloc fehlschl�gt
		if(deleteArray == NULL)
		{
			error(0);
		}
	}
	
	// Stein wird dem L�sch-Array hinzugef�gt
	// x-Koordinate
	deleteArray[deleteInUse] = columnindex;
	// y-Koordinate
	deleteArray[deleteInUse + 1] = thisHeight;
	
	// deleteInUse wird erh�ht
	deleteInUse = deleteInUse + 2;
	
}





// Funktion, die alle markierten Steine l�scht
void deleteMarked(void)
{
	
	int i;
	for(i = 0; i < deleteInUse; i = i + 2)
	{
		
		// x- und y-Koordinate des zu l�schenden Steins werden beschafft
		int column = deleteArray[i];
		int height = deleteArray[i + 1] - 1;
		
		
		// Da der zu l�schende Stein durch vorherige L�schungen schon nach unten verschieben sein k�nnte, muss er nochmal gesucht werden. Ausgangspunkt sind die gegebenen Koordinaten
		while(1)
		{
			// Wir k�nnen ab hier die Steine �berpr�fen
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
							// Der Stein wird �berschrieben
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
				// Die Spalte hat sich verkleinert und es gibt hier keine Steine auf die wir zugreifen k�nnten
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
	
	
	// deleteInUse wird zur�ckgesetzt
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
