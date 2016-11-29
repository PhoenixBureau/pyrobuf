import sys
import proto3_parser_base


Parser = proto3_parser_base.ProtobufParser


def parse(text):
  return Parser().parse(text, rule_name='proto', semantics=Semantics())


class Semantics(proto3_parser_base.ProtobufSemantics):

  def proto(self, ast): return Proto(ast)
  def import_(self, ast): return Import(ast)
  def option(self, ast): return Option(**ast)
  def field(self, ast): return Field(**ast)
  def enum(self, ast): return Enum(**ast)
  def enumField(self, ast): return EnumField(**ast)
  def message(self, ast): return Message(**ast)

  def decimalLit(self, ast): return int(ast)
  def octalLit(self, ast): return int(ast, 8)
  def hexLit(self, ast): return int(ast, 16)
  def boolLit(self, ast): return ast == 'true'

  def optionName(self, ast):
    a = ast.a if isinstance(ast.a, basestring) else '(' + '.'.join(ast.a) + ')'
    if ast.b:
      a = a + '.' + '.'.join(ast.b)
    return a


class Proto(object):

  def __init__(self, body):
    self.imports = []
    self.options = {}
    self.messages = {}
    self.enums = {}
    for thing in body:
      if isinstance(thing, Option): self.options[thing.name] = thing.value
#      elif isinstance(thing, Package): self.package = thing.name  # Or something...
      elif isinstance(thing, Import): self.imports.append(thing.what)
      elif isinstance(thing, Enum): self.enums[thing.name] = thing
      elif isinstance(thing, Message): self.messages[thing.name] = thing
      elif thing != ';':
        print >> sys.stderr, thing
        raise Exception # Just flip the table and go home...

  def __repr__(self):
    return 'Proto<%s>' % id(self)

  def report(self):
    print self
    print 'Imports'
    for imp in self.imports:
      print ' ', imp
    print 'Options'
    for opt in sorted(self.options):
      print ' ', opt, '=', self.options[opt]
    print 'Enums'
    for enu in sorted(self.enums):
      print ' ', enu
      e = self.enums[enu]
      for opt in sorted(e.options):
        print '   ', opt, '=', e.options[opt]
      for field in sorted(e.fields.values(), key=lambda ef: ef.number):
        print '   ', field.name, '=', field.number, field.options or ''      
    print 'Messages'
    for msg in self.messages:
      self.messages[msg].report()


class Enum(object):

  def __init__(self, name, body):
    self.name = name
    self.fields = {}
    self.options = {}
    for thing in body:
      if isinstance(thing, Option): self.options[thing.name] = thing.value
      elif isinstance(thing, EnumField): self.fields[thing.name] = thing
      elif thing != ';':
        print >> sys.stderr, thing
        raise Exception # Just flip the table and go home...

  def __repr__(self):
    return 'Enum("%(name)s")' % self.__dict__


class Message(object):

  def __init__(self, name, body):
    self.name = name
    self.fields = {}
    self.enums = {}
    self.messages = {}
    self.options = {}
    for thing in body:
      if isinstance(thing, Field): self.fields[thing.name] = thing
      elif isinstance(thing, Enum): self.enums[thing.name] = thing
      elif isinstance(thing, Message): self.messages[thing.name] = thing
      elif isinstance(thing, Option): self.options[thing.name] = thing.value
      elif thing != ';':
        print >> sys.stderr, thing
        raise Exception # Just flip the table and go home...

  def __repr__(self):
    return 'Message("%(name)s")' % self.__dict__

  def report(self, indent=1):
    i = ' ' * (2 * indent - 1)
    print i, 'message', self.name
    indent += 1
    i = ' ' * (2 * indent - 1)
    for opt in sorted(self.options):
      print i, opt, '=', self.options[opt]
    for enu in sorted(self.enums):
      print i, enu
      e = self.enums[enu]
      for opt in sorted(e.options):
        print i + '  ', opt, '=', e.options[opt]
      for field in sorted(e.fields.values(), key=lambda ef: ef.number):
        print i + '  ', field.name, '=', field.number, field.options or ''
    for field in sorted(self.fields.values(), key=lambda ef: ef.number):
      print i, field.name, '=', field.number, field.options or ''
    for msg in self.messages:
      self.messages[msg].report(indent)


class Option(object):

  def __init__(self, name, value):
    self.name = name
    self.value = value

  def __repr__(self):
    return 'Option("%(name)s", %(value)s)' % self.__dict__


class Field(object):

  def __init__(self, name, number, options, repeated, type_):
    self.name = name
    self.number = number
    self.options = {option.name: option.value for option in options or []}
    self.repeated = bool(repeated)
    self.type_ = type_

  def __repr__(self):
    return 'Field("%(name)s", %(number)i, %(options)s, %(repeated)s, %(type_)s)' % self.__dict__
#    return 'Field("%(name)s", %(number)i)' % self.__dict__


class EnumField(object):

  def __init__(self, name, number, options):
    self.name = name
    self.number = number
    self.options = {option.name: option.value for option in options or []}

  def __repr__(self):
    return 'EnumField("%(name)s", %(number)i, %(options)s)' % self.__dict__


class Import(object):

  def __init__(self, what):
    self.what = what

  def __repr__(self):
    return 'Import(%s)' % (self.what,)


if __name__ == '__main__':

  PROTO = '''\
  syntax = "proto3";
  import public "other.proto";
  option java_package = "com.example.foo";
  enum EnumAllowingAlias {
    option allow_alias = true;
    UNKNOWN = 0;
    STARTED = 1;
    RUNNING = 2 [(cus.tom_opt.ion) = "hello world"];
    ;
  }
  message outer {
    option (my_option).a = true;
    message inner {
      int64 ival = 1;
    }
    repeated inner inner_message = 2;
    EnumAllowingAlias enum_field = 3;
    bytes a_field_with_options = 4 [foo=23];
  }
  '''
  parser = Parser()
  prot = parser.parse(PROTO, rule_name='proto', semantics=Semantics())
  prot.report()
