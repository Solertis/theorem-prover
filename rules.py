#!/usr/bin/python -O
# -*- coding: utf-8 -*-

from axioms import *

##############################################################################
# Unification
##############################################################################

def unify(term_a, term_b):
  if isinstance(term_a, UnificationTerm):
    if term_b.occurs(term_a):
      return None
    return { term_a: term_b }
  if isinstance(term_b, UnificationTerm):
    if term_a.occurs(term_b):
      return None
    return { term_b: term_a }
  if isinstance(term_a, Variable) and isinstance(term_b, Variable):
    if term_a == term_b:
      return { }
    return None
  if (isinstance(term_a, Function) and isinstance(term_b, Function)) or \
     (isinstance(term_a, Predicate) and isinstance(term_b, Predicate)):
    if term_a.name != term_b.name:
      return None
    if len(term_a.terms) != len(term_b.terms):
      return None
    substitution = { }
    for i in range(len(term_a.terms)):
      a = term_a.terms[i]
      b = term_b.terms[i]
      for key in substitution:
        a = a.replace(key, substitution[key])
        b = b.replace(key, substitution[key])
      sub = unify(a, b)
      if sub == None:
        return None
      for key in sub:
        substitution[key] = sub[key]
    return substitution
  return None

##############################################################################
# Sequents
##############################################################################

class Sequent:
  def __init__(self, left, right):
    self.left = left
    self.right = right

  def fv(self):
    result = set()
    for formula in self.left:
      result |= formula.fv()
    for formula in self.right:
      result |= formula.fv()
    return result

  def getUnusedVariableName(self, prefx):
    fv = self.fv()
    index = 1
    name = prefx + str(index)
    while Variable(name) in fv:
      index += 1
      name = prefx + str(index)
    return name

  def isAxiomaticallyTrue(self):
    for formula_left in self.left:
      for formula_right in self.right:
        if unify(formula_left, formula_right) is not None:
          return True
    return False

  def __str__(self):
    return ", ".join([str(formula) for formula in self.left]) + " ⊢ " + \
      ", ".join([str(formula) for formula in self.right])

##############################################################################
# Proof search
##############################################################################

class SearchResult(Exception):
  def __init__(self, result):
    self.result = result

# returns True if the sequent is provable
# returns False or loops forever if the sequent is not provable
def proofGenerator(sequent):
  frontier = [sequent]
  visited = { sequent }
  depths = { } # keeps track of the number of times a ForAll left or ThereExists right has been used

  while len(frontier) > 0:
    # get the next sequent
    old_sequent = frontier.pop(0)
    print old_sequent
    if old_sequent.isAxiomaticallyTrue():
      continue
    
    # attempt to reduce a formula in the sequent
    reduced = False

    # left side (excluding ForAll)
    for formula in old_sequent.left:
      yield
      if isinstance(formula, Variable):
        continue
      if isinstance(formula, Function):
        continue
      if isinstance(formula, Predicate):
        continue
      if isinstance(formula, Not):
        new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent.left.remove(formula)
        new_sequent.right.add(formula.formula)
        if new_sequent not in visited:
          frontier.append(new_sequent)
          visited.add(new_sequent)
          reduced = True
          break
      if isinstance(formula, And):
        new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent.left.remove(formula)
        new_sequent.left.add(formula.formula_a)
        new_sequent.left.add(formula.formula_b)
        if new_sequent not in visited:
          frontier.append(new_sequent)
          visited.add(new_sequent)
          reduced = True
          break
      if isinstance(formula, Or):
        new_sequent_a = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent_b = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent_a.left.remove(formula)
        new_sequent_b.left.remove(formula)
        new_sequent_a.left.add(formula.formula_a)
        new_sequent_b.left.add(formula.formula_b)
        frontier.append(new_sequent_a)
        frontier.append(new_sequent_b)
        if new_sequent_a not in visited:
          frontier.append(new_sequent_a)
          visited.add(new_sequent_a)
          reduced = True
        if new_sequent_b not in visited:
          frontier.append(new_sequent_b)
          visited.add(new_sequent_b)
          reduced = True
        if reduced:
          break
      if isinstance(formula, Implies):
        new_sequent_a = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent_b = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent_a.left.remove(formula)
        new_sequent_b.left.remove(formula)
        new_sequent_a.right.add(formula.formula_a)
        new_sequent_b.left.add(formula.formula_b)
        if new_sequent_a not in visited:
          frontier.append(new_sequent_a)
          visited.add(new_sequent_a)
          reduced = True
        if new_sequent_b not in visited:
          frontier.append(new_sequent_b)
          visited.add(new_sequent_b)
          reduced = True
        if reduced:
          break
      if isinstance(formula, ThereExists):
        variable = Variable(old_sequent.getUnusedVariableName("v"))
        new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent.left.remove(formula)
        new_sequent.left.add(formula.formula.replace(formula.variable, variable))
        if new_sequent not in visited:
          frontier.append(new_sequent)
          visited.add(new_sequent)
          reduced = True
          break
    if reduced:
      continue

    # right side (excluding ThereExists)
    for formula in old_sequent.right:
      yield
      if isinstance(formula, Variable):
        continue
      if isinstance(formula, Function):
        continue
      if isinstance(formula, Predicate):
        continue
      if isinstance(formula, Not):
        new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent.right.remove(formula)
        new_sequent.left.add(formula.formula)
        if new_sequent not in visited:
          frontier.append(new_sequent)
          visited.add(new_sequent)
          reduced = True
          break
      if isinstance(formula, And):
        new_sequent_a = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent_b = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent_a.right.remove(formula)
        new_sequent_b.right.remove(formula)
        new_sequent_a.right.add(formula.formula_a)
        new_sequent_b.right.add(formula.formula_b)
        if new_sequent_a not in visited:
          frontier.append(new_sequent_a)
          visited.add(new_sequent_a)
          reduced = True
        if new_sequent_b not in visited:
          frontier.append(new_sequent_b)
          visited.add(new_sequent_b)
          reduced = True
        if reduced:
          break
      if isinstance(formula, Or):
        new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent.right.remove(formula)
        new_sequent.right.add(formula.formula_a)
        new_sequent.right.add(formula.formula_b)
        if new_sequent not in visited:
          frontier.append(new_sequent)
          visited.add(new_sequent)
          reduced = True
          break
      if isinstance(formula, Implies):
        new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent.right.remove(formula)
        new_sequent.left.add(formula.formula_a)
        new_sequent.right.add(formula.formula_b)
        if new_sequent not in visited:
          frontier.append(new_sequent)
          visited.add(new_sequent)
          reduced = True
          break
      if isinstance(formula, ForAll):
        variable = Variable(old_sequent.getUnusedVariableName("v"))
        new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
        new_sequent.right.remove(formula)
        new_sequent.right.add(formula.formula.replace(formula.variable, variable))
        if new_sequent not in visited:
          frontier.append(new_sequent)
          visited.add(new_sequent)
          reduced = True
          break
    if reduced:
      continue

    # ForAll (left)
    forall_left_formula = None
    forall_left_depth = None
    for formula in old_sequent.left:
      if isinstance(formula, ForAll):
        if formula in depths:
          depth = depths[formula]
          if forall_left_depth is None or forall_left_depth > depth:
            forall_left_formula = formula
            forall_left_depth = depth
        else:
          forall_left_formula = formula
          forall_left_depth = 0
          depths[formula] = 0

    # ThereExists (right)
    thereexists_right_formula = None
    thereexists_right_depth = None
    for formula in old_sequent.right:
      if isinstance(formula, ThereExists):
        if formula in depths:
          depth = depths[formula]
          if thereexists_right_depth is None or thereexists_right_depth > depth:
            thereexists_right_formula = formula
            thereexists_right_depth = depth
        else:
          thereexists_right_formula = formula
          thereexists_right_depth = 0
          depths[formula] = 0

    # apply the shallowest ForAll (left) / ThereExists (right)
    apply_left = False
    apply_right = False
    if forall_left_formula is not None and thereexists_right_formula is None:
      apply_left = True
    if forall_left_formula is None and thereexists_right_formula is not None:
      apply_right = True
    if forall_left_formula is not None and thereexists_right_formula is not None:
      if forall_left_depth < thereexists_right_depth:
        apply_left = True
      else:
        apply_right = True
    if apply_left:
      depths[forall_left_formula] += 1
      new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
      new_sequent.left.add(forall_left_formula.formula.replace(forall_left_formula.variable, UnificationTerm(old_sequent.getUnusedVariableName("t"))))
      if new_sequent not in visited:
        frontier.append(new_sequent)
        visited.add(new_sequent)
        reduced = True
    if apply_right:
      depths[thereexists_right_formula] += 1
      new_sequent = Sequent(old_sequent.left.copy(), old_sequent.right.copy())
      new_sequent.right.add(thereexists_right_formula.formula.replace(thereexists_right_formula.variable, UnificationTerm(old_sequent.getUnusedVariableName("t"))))
      if new_sequent not in visited:
        frontier.append(new_sequent)
        visited.add(new_sequent)
        reduced = True
    if reduced:
      continue
    
    # nothing more to reduce (i.e., we got stuck)
    raise SearchResult(False)

  # no more sequents to prove
  raise SearchResult(True)

# returns True if the sequent is provable
# returns False or loops forever if the sequent is not provable
def proveSequent(sequent):
  g = proofGenerator(sequent)
  while True:
    try:
      g.next()
    except SearchResult as r:
      return r.result

# returns True if the formula is provable from the axioms
# returns False or loops forever if the formula is not provable from the axioms
def proveFormula(formula):
  return proveSequent(Sequent(axioms, { formula }))

# returns True if the formula is provable from the axioms
# returns False if its inverse is provable from the axioms
# returns None or loops forever if its veracity is independent of the axioms
def proveOrDisproveFormula(formula):
  g = proofGenerator(proveSequent(Sequent(axioms, { formula })))
  h = proofGenerator(proveSequent(Sequent(axioms, { Not(formula) })))
  while g is not None or h is not None:
    if g is not None:
      try:
        g.next()
      except SearchResult as r:
        if r.result:
          return True
        else:
          g = None
    if h is not None:
      try:
        h.next()
      except SearchResult as r:
        if r.result:
          return False
        else:
          h = None
  return None