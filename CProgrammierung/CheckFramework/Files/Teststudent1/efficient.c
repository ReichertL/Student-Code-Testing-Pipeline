#include <stdio.h>


struct container {
  struct container* next;
  unsigned int ship;
};

struct stack {
  struct stack* next;
  struct container* bottom;
  struct container* top;
};


// read one line from the input file, return pointer to first container of that day
struct container* read_input_line(FILE* infile) {

  char buffer[11];  // 32 bit unsigned integer needs at most 10 digits!
  char read_digits;
  char c;
  struct container* first_container;
  struct container* last_container;
  struct container* new_container;

  first_container = 0;
  read_digits = 0;

  while (1) {

    c = fgetc(infile);

    if (c >= '0' && c <= '9') {  // found a digit
      if (read_digits < 10) {
        buffer[read_digits] = c;
        read_digits++;
      } else {
        printf("Invalid input, too long sequence of digits\n");
        exit(2);
      }

    } else if (c == ',' || c == '\n' || c == EOF) {

      if ((c == ',' || first_container) && read_digits == 0) {
        // - a comma may not appear before some digits have been read
        // - it may also not appear at the end of a line
        // - but completely empty lines are allowed!
        printf("Invalid input, bad comma\n");
        exit(2);
      }

      if (read_digits > 0) {
        // completed reading a ship ID, add a container to the list of containers
        new_container = malloc(sizeof(struct container));
        buffer[read_digits] = 0;
        new_container->ship = atoi(buffer);
        new_container->next = 0;
        if (!first_container) {
          first_container = new_container;
          last_container = new_container;
        } else {
          last_container->next = new_container;
          last_container = new_container;
        }
  
        // clear the buffer for the next input
        read_digits = 0;
      }

      // end of day
      if (c == '\n' || c == EOF) {
        if (!first_container && c == EOF) exit(0);  // done
        return first_container;
      }

    } else {
      printf("Invalid input, an invalid character has been encountered: %c\n", c);
      exit(2);
    }

  }

}


// adds a new container with the given ship id to an existing stack (with min. 1 existing container)
void add_container(struct container* cont, struct stack* dest_stack) {

  cont->next = 0;
  dest_stack->top->next = cont;
  dest_stack->top = cont;

}


// place container optimally given an existing set of stacks
struct stack* add_container_optimally(struct container* cont, struct stack* first_stack) {

  struct stack* best_stack;
  struct stack* current_stack;
  struct container* new_container;

  best_stack = 0;

  for (current_stack = first_stack; current_stack != 0; current_stack = current_stack->next) {
    if (current_stack->top->ship >= cont->ship && (best_stack == 0 || current_stack->top->ship < best_stack->top->ship))
      best_stack = current_stack;
  }

  if (best_stack) {
    // a good stack to add this one exists
    add_container(cont, best_stack);

    // the list of stacks remains unchanged
    return first_stack;

  } else {

    // we have to put the new container on a new stack
    best_stack = malloc(sizeof(struct stack));
    best_stack->next = first_stack;
    best_stack->bottom = cont;
    best_stack->top = cont;
    cont->next = 0;

    // the new stack is the new entry point into the list of stacks
    return best_stack;

  }

}


// output the number and list of stacks
void output(struct stack* first_stack) {

  unsigned int stack_count;
  struct stack* current_stack;
  struct container* current_container;

  // count the stacks
  stack_count = 0;
  for (current_stack = first_stack; current_stack != 0; current_stack = current_stack->next) stack_count++;

  // output stack count
  printf("%d", stack_count);

  // iterate stacks
  for (current_stack = first_stack; current_stack != 0; current_stack = current_stack->next) {

    printf(" ");

    // iterate containers in current stack
    for (current_container = current_stack->bottom; current_container != 0; current_container = current_container->next) {
      printf("%d", current_container->ship);
      if (current_container->next) printf(",");
    }

  }

  printf("\n");

}


// free the allocated memory for the stack structure
void free_stack_structure(struct stack* first_stack) {

  struct stack* current_stack;
  struct stack* next_stack;
  struct container* current_container;
  struct container* next_container;

  current_stack = first_stack;
  while (current_stack != 0) {
    next_stack = current_stack->next;
    current_container = current_stack->bottom;
    while (current_container != 0) {
      next_container = current_container->next;
      free(current_container);
      current_container = next_container;
    }
    free(current_stack);
    current_stack = next_stack;
  }

}


int main(int argc, char** argv) {

  struct stack* first_stack;
  FILE* infile;
  struct container* input;
  struct container* cont;

  // check number of command line arguments
  if (argc != 2) {
    printf("Usage: %s filename\n", argv[0]);
    exit(1);
  }

  infile = fopen(argv[1], "r");
  if (!infile) {
    printf("Input file %s does not exist or is not readable\n", argv[1]);
    exit(3);
  }

  while (!feof(infile)) {

    first_stack = 0;

    input = read_input_line(infile);

    while (input != 0) {

      // get next container from input list
      cont = input;
      input = input->next;

      first_stack = add_container_optimally(cont, first_stack);

    }

    output(first_stack);

    free_stack_structure(first_stack);

  }

  fclose(infile);

}
