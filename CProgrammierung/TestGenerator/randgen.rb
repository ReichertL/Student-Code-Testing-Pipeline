#!/usr/bin/ruby

NUMTASKS = 5

def numships
  #rand(9) + 1
  9
end

def shipids(num_ships)
  a = Array.new(num_ships) { |i|  rand(9) + 1 }
  a.each_index { |i|  a[i] = rand(9) + 1 while i>0 and a[0..(i-1)].include?(a[i]) }
  a
end

def numcontainers
  #rand(1000) + 1
  15
end


NUMTASKS.to_i.times do
  num_ships = numships
  ship_ids = shipids(num_ships)
  puts Array.new(numcontainers) { |i|  ship_ids[rand(num_ships)] }.join(",")
end
