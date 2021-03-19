
#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>

// *****************
// *   CONSTANTS   *
// *****************

// Initial and minimum column array size
#define MIN_COL_SIZE 4

// Initial playground changes array size
#define INITIAL_CHANGES_SIZE 8

// Initial piece removal array size
#define INITIAL_REMOVAL_SIZE 16

// Empty piece value
#define PIECE_EMPTY 255

// Min number of pieces required to form a line
#define MIN_LINE_COUNT 4

// Maximum absolute x value (1 digit more may not be able to fit into long)
#define MAX_X 999999999

// ********************
// *   HEADER TYPES   *
// ********************

// Value range: [0, 254], 255 = cleared
typedef unsigned char piece;

// Col types
typedef enum { COL_PIECES, COL_PADDING } colType;

// Col data structure
struct Col {
  // Col type
  colType type;

  // Depending on the type:
  // - DEFAULT: Number of pieces stacked on top of each other in this col
  // - PADDING: Number of padding cols between the previous and the next col
  unsigned long size;

  // Number of pieces that are part of the array
  unsigned long count;

  // Piece index above which changes were applied.
  // Equal to the col size if there are no changes.
  unsigned long changeY;

  // Pointer to next col
  struct Col* next;

  // Pointer to previous col
  struct Col* prev;

  // Column pieces
  piece pieces[];
};

// Data structure describing a single piece removal from a referenced column
struct PieceRemoval {
  // Pointer to the col a piece should be removed from
  struct Col *col;
  
  // Piece Y-position inside the reference col
  unsigned long y;
};

// Playground data structure (doubly linked list of cols)
struct Playground {
  // Pointer to col at the lower extreme
  struct Col* startCol;

  // Position of col at the lower extreme
  long startColX;

  // Pointer to origin col at x = 0
  struct Col* originCol;

  // Pointer to col at the upper extreme
  struct Col* endCol;

  // Position of col at the lower extreme
  long endColX;

  // Pointer to the iterator col
  struct Col* currentCol;

  // Position of the iterator col
  long currentX;

  // Array of changed cols (no duplicates allowed)
  struct Col** changedCols;
  unsigned long changedColsCount;
  unsigned long changedColsSize;
  
  // Removals
  struct PieceRemoval* pieceRemovals;
  unsigned long pieceRemovalsCount;
  unsigned long pieceRemovalsSize;
};

// ************************
// *   HEADER FUNCTIONS   *
// ************************

struct Playground* createPlayground(void);
void freePlayground(struct Playground* playground);
struct Col* createCol(void);
struct Col* resizeCol(struct Playground* playground, struct Col* col, unsigned long size);
struct Col* createPaddingCol(unsigned long size);
struct Col* playgroundGetCol(struct Playground* playground, long x);
void playgroundRemoveCol(struct Playground* playground, struct Col* col);
void playgroundPlacePiece(struct Playground* playground, long x, piece p);
void playgroundRemoveLines(struct Playground* playground);
void playgroundRemovePiece(struct Playground* playground, struct Col* col, unsigned long y);
void playgroundTrackChange(struct Playground* playground, struct Col* col, unsigned long y);
void playgroundCauseGravity(struct Playground* playground);
void playgroundPrint(struct Playground* playground);
void handleOutOfMemory(char description[]);

// ************
// *   BODY   *
// ************

/**
 * Global debug flag
 */
bool debug = false;

/**
 * Global playground instance
 */
struct Playground* playground;

/**
 * Main entry point
 * @return Exit code
 */
int main(int argc, char *argv[]) {
  // Create empty playground
  playground = createPlayground();
  
  // Debug mode: Run specific test case in debug mode if first argument is set
  if (argc == 2) {
    debug = true;
    freopen(argv[1], "r", stdin);
  }

  // Expected line format: ^[0-9]+ +-?[0-9]+$
  // Current line reading stage
  // -1 - Unexpected input
  //  0 - Reading piece in [0; 255]
  //  1 - Reading spaces and optional -
  //  2 - Reading positive x value in [0; +2^21]
  //  3 - Reading negative x value in [-2^21; 0]
  //  4 - No lines read
  short readingStage = 4;
  
  // Value currently being read
  long argValue = 0;
  
  // Read first line
  char *line = NULL;
  size_t lineSize = 32;
  long lineLength = getline(&line, &lineSize, stdin);
  
  short i;
  piece p = 0;
  long x = 0;
  
  // Iterate through lines
  while (lineLength > 0) {
    readingStage = 0;
    argValue = 0;
    i = -1;
    
    // Iterate through line characters
    while (++i < lineLength && readingStage != -1) {
      unsigned char c = line[i];
      if (c >= '0' && c <= '9') {
        // Read decimal digit
        if (readingStage == 1) {
          // Move to positive x reading stage
          readingStage = 2;
        }
        // Shift in decimal digit
        argValue = argValue * 10 + (c - '0');
        // Verify value bounds
        if (argValue > MAX_X) {
          readingStage = -1;
        }
      } else if (readingStage < 2 && c == ' ') {
        // Move to spaces stage
        readingStage = 1;
         
        if (argValue < PIECE_EMPTY) {
          p = argValue;
          argValue = 0;
        } else {
          // Unexpected piece value
          readingStage = -1;
        }
      } else if (readingStage == 1 && c == '-') {
        // Move to negative x reading stage
        readingStage = 3;
      } else if (c == '\n') {
        // Ignore newline characters
      } else {
        // Unexpected character
        readingStage = -1;
      }
    }
    
    if (readingStage < 2) {
      // Unexpected character
      break;
    }
    
    // Set x position
    x = readingStage == 2 ? argValue : -argValue;
    
    // Place piece p at x
    playgroundPlacePiece(playground, x, p);
    
    if (debug) {
      playgroundPrint(playground);
    }
    
    // Read next line
    lineLength = getline(&line, &lineSize, stdin);
  }
  
  // Free line
  free(line);
  
  // Handle unexpected input
  if (readingStage < 2) {
    fprintf(stderr, "Unexpected input. Expected line format: ^[0-9]+ +-?[0-9]+$\n");
    freePlayground(playground);
    exit(1);
  }

  // Print playground to stout
  playgroundPrint(playground);

  // Dealloc used memory before quitting
  freePlayground(playground);
  return 0;
}

/**
 * Handle the event of running out of memory.
 * @param description Task at which the program ran out of memory
 */
void handleOutOfMemory(char description[]) {
  fprintf(stderr, "Not enough memory left to %s.\n", description);
  freePlayground(playground);
  playground = NULL;
  exit(1);
}

/**
 * Create empty playground (containing a single origin node).
 * Assumptions:
 * - Origin, start and end cols must not be of type padding
 * - Two adjancent padding cols are not allowed
 * @return Pointer to playground
 */
struct Playground* createPlayground() {
  struct Playground* playground = (struct Playground*) malloc(
    sizeof(struct Playground));
  if (!playground) {
    handleOutOfMemory("create a playground");
  }

  struct Col* col = createCol();
  playground->originCol = col;
  playground->startCol = col;
  playground->startColX = 0;
  playground->endCol = col;
  playground->endColX = 0;
  playground->currentCol = col;
  playground->currentX = 0;
  
  playground->changedColsSize = INITIAL_CHANGES_SIZE;
  playground->changedColsCount = 0;
  playground->changedCols = (struct Col**)
    malloc(playground->changedColsSize * sizeof(struct Col*));
  if (!playground->changedCols) {
    handleOutOfMemory("create a playground");
  }
  
  playground->pieceRemovalsSize = INITIAL_REMOVAL_SIZE;
  playground->pieceRemovalsCount = 0;
  playground->pieceRemovals = (struct PieceRemoval*)
    malloc(playground->pieceRemovalsSize * sizeof(struct PieceRemoval));
  if (!playground->pieceRemovals) {
    handleOutOfMemory("create a playground");
  }
  
  return playground;
}

/**
 * Frees a playground instance with all of its cols.
 * @param playground Playground instance to free
 */
void freePlayground(struct Playground* playground) {
  if (playground) {
    // Free cols in playground
    struct Col* col = playground->startCol;
    struct Col* next;
    while (col) {
      next = col->next;
      free(col);
      col = next;
    }
    
    // Free piece removal and change arrays
    free(playground->changedCols);
    free(playground->pieceRemovals);

    // Free playground itself
    free(playground);
  }
}

/**
 * Create a col node with the default initial size.
 * @return Pointer to new col node
 */
struct Col* createCol() {
  struct Col* col = (struct Col*)
    malloc(sizeof(struct Col) + sizeof(piece) * MIN_COL_SIZE);
  if (!col) {
    handleOutOfMemory("create a column");
  }
  col->type = COL_PIECES;
  col->size = MIN_COL_SIZE;
  col->count = 0;
  col->changeY = MIN_COL_SIZE;
  col->next = NULL;
  col->prev = NULL;
  return col;
}

/**
 * Resize a col node to the given size.
 * @param playground Pointer to playground the col is situated in.
 * Needed to update the playground pointers to the resized col pointer.
 * @param col Pointer to col to be resized
 * @param size Size the col should be resized to
 * @return Pointer to resized col node
 */
struct Col* resizeCol(struct Playground* playground, struct Col* col, unsigned long size) {
  if (size < MIN_COL_SIZE) {
    size = MIN_COL_SIZE;
  }
  
  if (col->size == size) {
    return col;
  }
  
  struct Col* resizedCol = (struct Col*)
    realloc(col, sizeof(struct Col) + sizeof(piece) * size);
  if (!resizedCol) {
    handleOutOfMemory("resize a column");
  }
  
  // Update size and state
  if (resizedCol->changeY == resizedCol->size) {
    resizedCol->changeY = size;
  }
  resizedCol->size = size;
  
  // Update pointers
  if (resizedCol->next) {
    resizedCol->next->prev = resizedCol;
  } else {
    playground->endCol = resizedCol;
  }
  if (resizedCol->prev) {
    resizedCol->prev->next = resizedCol;
  } else {
    playground->startCol = resizedCol;
  }
  if (col == playground->originCol) {
    playground->originCol = resizedCol;
  }
  if (col == playground->currentCol) {
    playground->currentCol = resizedCol;
  }
  return resizedCol;
}

/**
 * Create a padding col node with the given size.
 * @param size Number of padding cols
 * @return Pointer to new col node
 */
struct Col* createPaddingCol(unsigned long size) {
  struct Col* col = (struct Col*) malloc(sizeof(struct Col));
  if (!col) {
    handleOutOfMemory("create a padding column");
  }
  col->type = COL_PADDING;
  col->size = size;
  col->next = NULL;
  col->prev = NULL;
  return col;
}

/**
 * Insert a piece at the given x-position.
 * @param playground Playground instance
 * @param x Position to insert the piece
 * @param p Piece color to be inserted
 */
void playgroundPlacePiece(struct Playground* playground, long x, piece p) {
  struct Col* col = playgroundGetCol(playground, x);

  // Dynamically increase col size if necessary
  if (col->count == col->size) {
    col = resizeCol(playground, col, col->size * 2);
  }

  // Append piece to the top of the col stack
  col->pieces[col->count] = p;
  playgroundTrackChange(playground, col, col->count);
  col->count++;

  // Scan for lines, remove them, cause gravity and repeat the process until no
  // more lines are being identified
  playgroundRemoveLines(playground);
  while (playground->pieceRemovalsCount > 0) {
    playgroundCauseGravity(playground);
    playgroundRemoveLines(playground);
  }

  // Reset change state and memory optimization (col shrinking and removal)
  for (unsigned long i = 0; i < playground->changedColsCount; i++) {
    col = playground->changedCols[i];
    if (col->count == 0 && col != playground->originCol) {
      // Found empty column not being at the origin, remove it
      playgroundRemoveCol(playground, col);
    } else if (col->size > MIN_COL_SIZE && col->count * 4 < col->size) {
      // Reset change state and shrink col
      col->changeY = col->size;
      col = resizeCol(playground, col, col->size / 4);
    } else {
      // Reset change state
      col->changeY = col->size;
    }
  }
  
  // Clear changes
  playground->changedColsCount = 0;
}

/**
 * Finds the Col at the given x. Lazily creates a col instance if not done, yet.
 * Lazily creates padding cols if necessary, but they are never returned.
 * Inside this method make sure the linked list stays intact between creation
 * calls to ensure the list can be freed up, again.
 * @param playground Playground instance
 * @param x Col position
 * @return Pointer to Col struct
 */
struct Col* playgroundGetCol(struct Playground* playground, long x) {
  struct Col* col;
  
  // Test basic search cases (cheap, in O(1))
  if (x == 0) {
    // Origin col requested
    return playground->originCol;

  } else if (x == playground->endColX) {
    // End col requested
    return playground->endCol;

  } else if (x > playground->endColX) {
    // Requested col exceeds end col

    // Append new padding col, if necessary
    if (playground->endColX + 1 < x) {
      col = createPaddingCol(x - (long) playground->endColX - 1);
      playground->endCol->next = col;
      col->prev = playground->endCol;
      playground->endCol = col;
    }

    // Append new col
    col = createCol();
    playground->endCol->next = col;
    col->prev = playground->endCol;
    playground->endCol = col;
    playground->endColX = x;

    return col;

  } else if (x == playground->startColX) {
    // Start col requested
    return playground->startCol;

  } else if (x < playground->startColX) {
    // Requested col exceeds start col

    // Prepend new padding col, if necessary
    if (playground->startColX - 1 > x) {
      col = createPaddingCol((long) playground->startColX - x - 1);
      playground->startCol->prev = col;
      col->next = playground->startCol;
      playground->startCol = col;
    }

    // Prepend new col
    col = createCol();
    playground->startCol->prev = col;
    col->next = playground->startCol;
    playground->startCol = col;
    playground->startColX = x;

    return col;
  }

  // The easiest cases of finding a col were tested above
  // Now we need to iterate to it (expensive)
  col = playground->currentCol;
  long i = playground->currentX;
  struct Col* newCol;
  
  // Move iterator until reaching the desired position or the end
  if (i <= x) {
    // Move iterator forward
    while (i < x) {
      i += col->type == COL_PADDING ? col->size : 1;
      col = col->next;
    }
  } else {
    // Move iterator backward
    while (i > x) {
      col = col->prev;
      i -= col->type == COL_PADDING ? col->size : 1;
    }
    if (i < x) {
      // Ran past the x col, col must be of type padding (with size > 1).
      // Move iterator behind that padding col resulting in the same situation
      // as when moving the iterator forward.
      i += col->size;
      col = col->next;
    }
  }

  if (i > x) {
    // Ran past the x col, col->prev must be of type padding (with size > 1)
    struct Col* lowerPadding = col->prev;

    // Reduce lower padding to insert new col after it
    lowerPadding->size -= i - x;

    // Append new col after lower padding
    newCol = createCol();
    newCol->prev = lowerPadding;
    lowerPadding->next = newCol;

    // Append optional upper padding, if necessary
    if (i - x > 1) {
      newCol = createPaddingCol(i - x - 1);
      newCol->prev = lowerPadding->next;
      newCol->prev->next = newCol;
    }

    // Connect new col(s) to the current col
    col->prev = newCol;
    newCol->next = col;
    col = lowerPadding->next;
  }

  if (col->type == COL_PADDING) {
    // Create new col and connect it to the lower neighbour
    newCol = createCol();
    newCol->prev = col->prev;
    col->prev->next = newCol;

    if (col->size == 1) {
      // Connect new col to the right neighbour, replacing the padding col
      newCol->next = col->next;
      newCol->next->prev = newCol;

      // Let go padding col
      free(col);
      col = newCol;
    } else {
      // Shrink down padding size by 1 and insert new col before it
      col->size--;
      newCol->next = col;
      col->prev = newCol;
      col = newCol;
    }
  }

  // Update iterator
  playground->currentCol = col;
  playground->currentX = x;
  return col;
}

/**
 * Remove the given col from the playground.
 * Maintain the playground positions and pointers (startCol, currentCol, endCol)
 * that must point to piece cols.
 * @param playground Playground instance
 * @param col Col to be removed. Must not be the origin col.
 */
void playgroundRemoveCol(struct Playground* playground, struct Col* col) {
  struct Col* prevCol = col->prev;
  struct Col* nextCol = col->next;
  
  if (prevCol && nextCol) {
    // The col has two adjacent cols
    if (prevCol->type == COL_PADDING && nextCol->type == COL_PADDING) {
      // Span the lower padding col over the upper padding col
      prevCol->next = nextCol->next;
      nextCol->next->prev = prevCol;
      prevCol->size += nextCol->size + 1;
      
      if (playground->currentCol == col) {
        playground->currentCol = prevCol->prev;
        playground->currentX -= prevCol->size - nextCol->size;
      }
      
      // Free dangling upper padding col
      free(nextCol);
      
    } else if (prevCol->type == COL_PADDING || nextCol->type == COL_PADDING) {
      // Remove col and expand lower or upper padding
      prevCol->next = nextCol;
      nextCol->prev = prevCol;
      if (prevCol->type == COL_PADDING) {
        prevCol->size++;
        
        if (playground->currentCol == col) {
          playground->currentCol = nextCol;
          playground->currentX++;
        }
      } else {
        nextCol->size++;
        
        if (playground->currentCol == col) {
          playground->currentCol = prevCol;
          playground->currentX--;
        }
      }
    } else {
      // Col in between other cols, replace piece col by padding col
      struct Col* paddingCol = createPaddingCol(1);
      prevCol->next = paddingCol;
      paddingCol->prev = prevCol;
      nextCol->prev = paddingCol;
      paddingCol->next = nextCol;
      
      if (playground->currentCol == col) {
        playground->currentCol = prevCol;
        playground->currentX--;
      }
    }

    // Free dangling col
    free(col);
  } else if (col == playground->startCol) {
    // The col to be removed is at the lower end
    // Remove col itself
    struct Col* startCol = col->next;
    free(startCol->prev);
    startCol->prev = NULL;
    playground->startColX++;
    
    // Remove dangling padding col
    if (startCol->type == COL_PADDING) {
      playground->startColX += startCol->size;
      startCol = startCol->next;
      free(startCol->prev);
      startCol->prev = NULL;
    }
    
    // Update pointers
    playground->startCol = startCol;
    if (playground->currentCol == col) {
      playground->currentCol = startCol;
      playground->currentX = playground->startColX;
    }
  } else if (col == playground->endCol) {
    // The col to be removed is at the upper end
    // Remove col itself
    struct Col* endCol = col->prev;
    free(endCol->next);
    endCol->next = NULL;
    playground->endColX--;
    
    // Remove dangling padding col
    if (endCol->type == COL_PADDING) {
      playground->endColX -= endCol->size;
      endCol = endCol->prev;
      free(endCol->next);
      endCol->next = NULL;
    }
    
    // Update pointers
    playground->endCol = endCol;
    if (playground->currentCol == col) {
      playground->currentCol = endCol;
      playground->currentX = playground->endColX;
    }
  }
}

/**
 * Identify horizontal (–), vertical (|), diagonal (/, \) lines and mark pieces
 * on those lines as empty while tracking changes.
 * @param playground Playground
 */
void playgroundRemoveLines(struct Playground* playground) {
  unsigned long j;
  long y;
  long nextY;
  unsigned long lineLength;
  signed short delY;

  piece currentPiece;
  piece lineColor;

  struct Col* col;
  struct Col* nextCol;
  struct Col* lineEndCol;
  struct Col* lineStartCol;

  // Only consider cols where changes were applied
  for (unsigned long i = 0; i < playground->changedColsCount; i++) {
    col = playground->changedCols[i];

    // For each y above changeY identify crossing horizontal and diagonal lines
    for (y = col->changeY; y < col->count; y++) {
      currentPiece = col->pieces[y];
      
      // TODO: No need to search from pieces that are marked as removed
      // Problem: The current data structure does not allow this in O(1)
      
      // Iterate through directions falling diagonal (-1), horizontal (0) and
      // climbing diagonal (1)
      for (delY = -1; delY <= 1; delY++) {
        // Upper col the current line is ending
        lineEndCol = col;

        // Next col piece Y-index
        nextCol = col->next;
        nextY = y + delY;

        // Line piece count
        lineLength = 1;
        
        // Move forward while there is a next col, the next col is not a padding
        // col, the next col is high enough and the next piece in it is of
        // the current color or empty
        while (
          // Next column availability
          nextCol &&
          nextCol->type == COL_PIECES &&
          // Bounds of y-position
          nextY >= 0 &&
          nextY < nextCol->count &&
          // Check piece color
          nextCol->pieces[nextY] == currentPiece
        ) {
          lineEndCol = nextCol;
          nextCol = lineEndCol->next;
          nextY += delY;
          lineLength++;
        }

        // Do the same moving backward
        lineStartCol = col;
        nextCol = col->prev;
        nextY = y - delY;

        while (
          // Next column availability
          nextCol &&
          nextCol->type == COL_PIECES &&
          // Bounds of y-position
          nextY >= 0 &&
          nextY < nextCol->count &&
          // Check piece color
          nextCol->pieces[nextY] == currentPiece
        ) {
          lineStartCol = nextCol;
          nextCol = lineStartCol->prev;
          nextY -= delY;
          lineLength++;
        }

        if (lineLength >= MIN_LINE_COUNT) {
          // We identified a horizontal or diagonal line (based on nextY)
          // Iterate over line cols and remove each piece
          nextY += delY;
          nextCol = lineStartCol;
          while (nextCol && nextCol->prev != lineEndCol) {
            playgroundRemovePiece(playground, nextCol, nextY);
            nextCol = nextCol->next;
            nextY += delY;
          }
        }
      }
    }

    // Remove all vertical lines above change mark in linear time
    lineColor = PIECE_EMPTY;
    lineLength = 0;

    for (y = col->count - 1; y >= 0; y--) {
      currentPiece = col->pieces[y];
      if (currentPiece == lineColor) {
        // Add piece to line
        lineLength++;
        if (lineLength == MIN_LINE_COUNT) {
          // Min line count fulfilled, remove pieces
          for (j = 0; j < MIN_LINE_COUNT; j++) {
            playgroundRemovePiece(playground, col, y + j);
          }
        } else if (lineLength > MIN_LINE_COUNT) {
          // Remove this next line piece
          playgroundRemovePiece(playground, col, y);
        }
      } else if (y >= col->changeY) {
        // Reset line
        lineColor = currentPiece;
        lineLength = 1;
      } else {
        // Below the change mark we can stop searching for new lines
        break;
      }
    }
  }
}

/**
 * Mark piece at the given Y-position inside a col as to be removed.
 * It will definetly be removed in the gravity step of the loop.
 * @param playground Playground instance
 * @param col Col instance to remove piece from
 * @param y Y-position of piece to be removed
 */
void playgroundRemovePiece(struct Playground* playground, struct Col* col, unsigned long y) {
  if (playground->pieceRemovalsCount == playground->pieceRemovalsSize) {
    // Dynamically increase piece removal array size
    playground->pieceRemovalsSize *= 2;
    playground->pieceRemovals = (struct PieceRemoval*) realloc(
      playground->pieceRemovals,
      playground->pieceRemovalsSize * sizeof(struct PieceRemoval)
    );
  }
  struct PieceRemoval *pieceRemoval =
    &playground->pieceRemovals[playground->pieceRemovalsCount++];
  pieceRemoval->col = col;
  pieceRemoval->y = y;
  playgroundTrackChange(playground, col, y);
}

/**
 * Track a col change at the given Y-position.
 * @param playground Playground instance
 * @param col Col instance that changed
 * @param y Piece Y-position
 */
void playgroundTrackChange(struct Playground* playground, struct Col* col, unsigned long y) {
  if (col->changeY == col->size) {
    // Column has not yet been marked as changed in the current iteration
    col->changeY = y;

    // Dynamically increase change array size, if necessary
    if (playground->changedColsCount == playground->changedColsSize) {
      playground->changedColsSize *= 2;
      playground->changedCols = (struct Col**) realloc(
        playground->changedCols,
        playground->changedColsSize * sizeof(struct Col*)
      );
    }
    
    // Append col to changed cols array
    playground->changedCols[playground->changedColsCount++] = col;
  } else if (col->changeY > y) {
    // Update Y-position of the change
    col->changeY = y;
  }
}

/**
 * Consumes the playground piece removals and lets pieces stacked above those
 * to be removed fall down. Updates the col count accordingly.
 * @param playground Playground instance
 */
void playgroundCauseGravity(struct Playground* playground) {
  unsigned long i;
  struct Col* col;
  struct PieceRemoval* pieceRemoval;
  
  // Iterate through removals and mark pieces as empty in the playground
  for (i = 0; i < playground->pieceRemovalsCount; i++) {
    pieceRemoval = &playground->pieceRemovals[i];
    pieceRemoval->col->pieces[pieceRemoval->y] = PIECE_EMPTY;
  }
  
  // Clear piece removals array
  playground->pieceRemovalsCount = 0;
  
  // Iterate through cols where changes were applied
  for (i = 0; i < playground->changedColsCount; i++) {
    col = playground->changedCols[i];

    // Cause gravity on a single column
    unsigned long removedPieces = 0;
    for (unsigned long y = col->changeY; y < col->count; y++) {
      if (col->pieces[y] == PIECE_EMPTY) {
        removedPieces++;
      } else {
        col->pieces[y - removedPieces] = col->pieces[y];
      }
    }

    // Update col piece count / height
    col->count -= removedPieces;
  }
}

/**
 * Print playground
 * @param playground Pointer to playground struct to be printed
 */
void playgroundPrint(struct Playground* playground) {
  struct Col* col = playground->startCol;
  long x = playground->startColX;
  
  if (!debug) {
    while (col) {
      if (col->type == COL_PIECES) {
        // Print column pieces
        for (long unsigned j = 0; j < col->count; j++) {
          printf("%d %ld %lu\n", col->pieces[j], x, j);
        }
        // Iterate to the next col
        x++;
        col = col->next;
      } else {
        // Iterate to the next col
        x = x + col->size;
        col = col->next;
      }
    }
  } else {
    printf("Playground: [%ld; %ld]", playground->startColX, playground->endColX);
    
    while (col) {
      if (col->type == COL_PIECES) {
        printf("\n[%8ld] col %2lu/%2lu |", x, col->count, col->size);

        // Print column pieces
        for (long unsigned j = 0; j < col->count; j++) {
          printf("%3hu|", col->pieces[j]);
        }
        // Iterate to the next col
        x++;
        col = col->next;
      } else {
        printf("\n[%8ld] --- %lu cols ---", x, col->size);

        // Iterate to the next col
        x = x + col->size;
        col = col->next;
      }
    }
    
    printf("\n\n");
  }
}
