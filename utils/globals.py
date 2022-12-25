from enum import Enum, auto


COLOR_EMBED_DARK = 0x2F3136


class ReminderChannel(Enum):
    Here = auto()
    DM = auto()


class ReminderType(Enum):
    Single = auto()
    Daily = auto()


class UnitType(Enum):
    Celsius = auto()
    Fahrenheit = auto()
    Kelvin = auto()
    Centimeter = auto()
    Meter = auto()
    Kilometer = auto()
    Inch = auto()
    Foot = auto()
    Yard = auto()
    Mile = auto()


ConversionTable = {

    # Temperature
    UnitType.Celsius: {UnitType.Fahrenheit: lambda x: (x * 1.8) + 32,
                       UnitType.Kelvin: lambda x: x + 273.15,
                       },
    UnitType.Fahrenheit: {UnitType.Celsius: lambda x: (x - 32) / 1.8,
                          UnitType.Kelvin: lambda x: (x - 32) / 1.8 + 273.15,
                          },
    UnitType.Kelvin: {UnitType.Celsius: lambda x: x - 273.15,
                      UnitType.Fahrenheit: lambda x: x * 1.8 - 459.67,
                      },

    # Length
    UnitType.Centimeter: {UnitType.Meter: lambda x: x / 100,
                          UnitType.Kilometer: lambda x: x / 100_000,
                          UnitType.Inch: lambda x: x / 2.54,
                          UnitType.Foot: lambda x: x / 30.48,
                          UnitType.Yard: lambda x: x / 91.44,
                          UnitType.Mile: lambda x: x / 160900
                          },
    UnitType.Meter: {UnitType.Centimeter: lambda x: x * 100,
                     UnitType.Kilometer: lambda x: x / 1000,
                     UnitType.Inch: lambda x: x * 39.37,
                     UnitType.Foot: lambda x: x * 3.281,
                     UnitType.Yard: lambda x: x * 1.094,
                     UnitType.Mile: lambda x: x * 1609
                     },
    UnitType.Kilometer: {UnitType.Centimeter: lambda x: x * 100_000,
                         UnitType.Meter: lambda x: x * 1000,
                         UnitType.Inch: lambda x: x * 39370,
                         UnitType.Foot: lambda x: x * 3281,
                         UnitType.Yard: lambda x: x * 1094,
                         UnitType.Mile: lambda x: x / 1.609
                         },
    UnitType.Inch: {UnitType.Centimeter: lambda x: x * 2.54,
                    UnitType.Meter: lambda x: x / 39.37,
                    UnitType.Kilometer: lambda x: x / 39370,
                    UnitType.Foot: lambda x: x / 12,
                    UnitType.Yard: lambda x: x / 36,
                    UnitType.Mile: lambda x: x / 63360,
                    },
    UnitType.Foot: {UnitType.Centimeter: lambda x: x * 30.48,
                    UnitType.Meter: lambda x: x / 3.281,
                    UnitType.Kilometer: lambda x: x / 3281,
                    UnitType.Inch: lambda x: x * 12,
                    UnitType.Yard: lambda x: x / 3,
                    UnitType.Mile: lambda x: x / 5280,
                    },
    UnitType.Yard: {UnitType.Centimeter: lambda x: x * 91.44,
                    UnitType.Meter: lambda x: x / 1.094,
                    UnitType.Kilometer: lambda x: x / 1094,
                    UnitType.Inch: lambda x: x * 36,
                    UnitType.Foot: lambda x: x * 3,
                    UnitType.Mile: lambda x: x / 1760,
                    },
    UnitType.Mile: {UnitType.Centimeter: lambda x: x * 160900,
                    UnitType.Meter: lambda x: x * 1609,
                    UnitType.Kilometer: lambda x: x * 1.609,
                    UnitType.Inch: lambda x: x * 63360,
                    UnitType.Foot: lambda x: x * 5280,
                    UnitType.Yard: lambda x: x * 1760,
                    },
}
