#include <stdio.h>


struct container {
  struct container* next;
  // the prev pointer is only used in stack data structures,
  // starting from the second-to-bottom container;
  // everywhere else it's value is undefined
  struct container* prev;    
  unsigned int ship;
};

struct stack {
  struct stack* next;
  struct stack* prev;
  struct container* bottom;
  struct container* top;
};

int best_num_stacks;


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


// create a new stack and append it to the stack list; return new last stack pointer
struct stack* add_stack(struct container* cont, struct stack* last_stack) {

  struct stack* new_stack;

  new_stack = malloc(sizeof(struct stack));
  new_stack->top = cont;
  new_stack->bottom = cont;
  new_stack->next = 0;
  new_stack->prev = last_stack;
  if (last_stack != 0) last_stack->next = new_stack;
  cont->next = 0;

  return new_stack;

}


// remove front stack from the end of a stack list; return new stack list entry pointer
// assumes the stack to be removed is already empty (i.e., no containers are freed)
struct stack* remove_stack(struct stack* last_stack) {

  struct stack* new_last_stack;

  new_last_stack = last_stack->prev;
  free(last_stack);
  if (new_last_stack) new_last_stack->next = 0;

  return new_last_stack;

}


// add a container on top of a stack
void push_to_stack(struct stack* s, struct container* c) {

  s->top->next = c;
  c->prev = s->top;
  s->top = c;
  c->next = 0;

}


// remove the top container from a stack; does not work for the bottom container!
void pop_from_stack(struct stack* s) {

  s->top = s->top->prev;
  s->top->next = 0;

}


void output_stack(struct container* first);
void output(struct stack* first_stack);


// try all placements of remaining input
void try_placements(struct container* input, struct stack* first_stack, struct stack* last_stack, int num_existing_stacks) {

  struct stack* current_stack;
  struct stack* optimal_stack;
  struct container* next_input;
  
//   printf("==========================\n");
//   printf("input = ");
//   output_stack(input);
//   printf("\nfirst_stack = %x, last_stack = %x\n", first_stack, last_stack);
//   printf("num_existing_stacks = %d\n", num_existing_stacks);
//   output(first_stack);
//   printf("==========================\n");

  // is it no longer possible to come to a better solution? then we don't need to continue in the current branch
  if (best_num_stacks >= 0  &&  num_existing_stacks >= best_num_stacks) {
//     printf("pruning\n");
    return;
  }

  if (input == 0) {
    // no further input, we found a new optimum! (otherwise we would have returned above)
    
    printf("found a new optimum with %d stacks\n", num_existing_stacks);
    best_num_stacks = num_existing_stacks;
    
    output(first_stack);
    
    printf("\n\n");
    
    // TODO save the container order for possible later output
    
    return;
  }

  // save a pointer to the remaining input, to restore the data structure later on
  next_input = input->next;

  // does a stack with the same ship ID on top exist?
  optimal_stack = 0;
  for (current_stack = first_stack; current_stack != 0; current_stack = current_stack->next) {
    if (current_stack->top->ship == input->ship) optimal_stack = current_stack;
  }

  if (optimal_stack) {
    // a stack where we can place this container in any case has been found, so we use it

    push_to_stack(optimal_stack, input);

    // try all combinations for subsequent input
    try_placements(next_input, first_stack, last_stack, num_existing_stacks);

    // restore data structures
    pop_from_stack(optimal_stack);
    input->next = next_input;

  } else {
    // there is no "perfect" stack for this container, so we have to try all other possibilities

    // first we try all existing stacks
    for (current_stack = first_stack; current_stack != 0; current_stack = current_stack->next) {

      if (current_stack->top->ship < input->ship) continue;  // may never put a higher ID on top of a lower one

      push_to_stack(current_stack, input);

      // try all combinations for subsequent input
      try_placements(next_input, first_stack, last_stack, num_existing_stacks);

      // restore data structures
      pop_from_stack(current_stack);
      input->next = next_input;
    }

    // finally we create a new stack for the container
    struct stack* new_last_stack = add_stack(input, last_stack);

    // try all combinations for subsequent input
    try_placements(next_input, first_stack ? first_stack : new_last_stack, new_last_stack, num_existing_stacks + 1);

    // restore data structures
    remove_stack(new_last_stack);
    input->next = next_input;
  }

}


void output_stack(struct container* first) {

  struct container* current_container;
  
  // iterate containers
  for (current_container = first; current_container != 0; current_container = current_container->next) {
    printf("%d", current_container->ship);
    if (current_container->next) printf(",");
  }

}


// output the number and list of stacks
void output(struct stack* first_stack) {

  unsigned int stack_count;
  struct stack* current_stack;

  // count the stacks
  stack_count = 0;
  for (current_stack = first_stack; current_stack != 0; current_stack = current_stack->next) stack_count++;

  // output stack count
  printf("%d", stack_count);

  // iterate stacks
  for (current_stack = first_stack; current_stack != 0; current_stack = current_stack->next) {
    printf(" ");
    output_stack(current_stack->bottom);
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

  FILE* infile;
  struct container* input;

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

    best_num_stacks = -1;
    
    printf("\n\nNEXT INPUT LINE\n\n");

    input = read_input_line(infile);

    try_placements(input, 0, 0, 0);

    // TODO: Output the result, cleanup memory

//     output(first_stack);

//     free_stack_structure(first_stack);

  }

  fclose(infile);

}
