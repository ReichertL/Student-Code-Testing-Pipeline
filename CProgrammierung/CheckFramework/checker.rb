#!/usr/bin/ruby

infile = File.open(ARGV[0])
testfile = STDIN

def solve(input)

  stacks = Array.new

  input.each do |id|

    dest = nil
    stacks.each do |stack|
      dest = stack if (not dest and stack.last >= id) or (dest and stack.last >= id and stack.last <= dest.last)
    end

    if not dest
      dest = Array.new
      stacks << dest
    end

    dest << id

  end

  return stacks

end


def feasible(input, testdata)

  return true if input.empty?

  # try all possibilities to place the first container and check whether the remaining problem is feasible
  testdata.each do |stack|
  
    next if stack.empty? or stack.first != input.first

    id = stack.shift
    input.shift
    success = feasible(input, testdata)

    # always keep care that this remain non-destructive!
    input.unshift id
    stack.unshift id
    
#     puts "success" if success
    return true if success
  
  end

#   puts "hm, doesn't work"
  return false

end


class Array

  def sum
    x = 0
    each { |i|  x += i }
    return x
  end
  
end


def dump_solutions(inputline, testline, optimal)
  print "          Input:            ", inputline
  print "          Output:           ", testline
  print "          Optimal solution: ", optimal.size, " ", optimal.collect{|s| s.join(",")}.join(" "), "\n"
end


infile.each_line do |inputline|
  begin
    input = inputline.split(",").collect{|id| id.to_i}
    optimal = solve(input)
    
    testline = testfile.readline
    testdata = testline.split(" ").collect{|s| s.split(",").collect{|i| i.to_i}}
    testnumstacks = testdata.shift.first
  
    puts
  rescue StandardError => bang
    break
  end
  
  # TEST 1: IS THE OUTPUT CONSISTENT?
  
  if testnumstacks != testdata.size
    puts "Rejected: reported stack count (#{testnumstacks}) and used stack count (#{testdata.size}) do not match"
    dump_solutions(inputline, testline, optimal)
    next
  end
  
  
  # TEST 2: IS THE USED NUMBER OF STACKS CORRECT?
  
  if testnumstacks > optimal.size
    puts "Rejected: #{testnumstacks} stacks are used, but the optimal solution requires only #{optimal.size}"
    dump_solutions(inputline, testline, optimal)
    next
  end
  
  if testnumstacks < optimal.size
    puts "Rejected: #{testnumstacks} stacks are used, although #{optimal.size} are necessary"
    dump_solutions(inputline, testline, optimal)
    next
  end
  
  
  # TEST 3: DOES THE TOTAL NUMBER OF CONTAINERS ON THE STACK MATCH THE TOTAL COUNT IN THE INPUT?
  
  if testdata.collect{|s| s.size}.sum != input.size
    puts "Rejected: the number of containers in the stacks (#{testdata.collect{|s| s.size}.sum}) doesn't match the number of containers in the input (#{input.size})"
    dump_solutions(inputline, testline, optimal)
    next
  end

  # TEST 4: IS THE GIVEN SOLUTION VALID?
  
  valid = true
  testdata.each do |stack|
    i = stack.first
    stack.each do |j|
      valid &&= i >= j
      i = j
    end
  end
  
  if not valid
    puts "Rejected: the given solution does not allow loading of ships in order of arrival"
    dump_solutions(inputline, testline, optimal)
    next
  end

  # TEST 5: IS IT POSSIBLE TO BUILD THE STACKS AS REPORTED?
  
  if not feasible(input, testdata)
    puts "Rejected: it is not possible to build the stacks in the given way"
    dump_solutions(inputline, testline, optimal)
    next
  end
  
  
  # HMM, THAT REALLY LOOKS OK NOW
  
  puts "Accepted"
  dump_solutions(inputline, testline, optimal)

end

puts
