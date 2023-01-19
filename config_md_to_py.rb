config_md = "/home/donn/efabless/openlane/docs/source/reference/configuration.md"
config_str = File.read(config_md)

var_rx = /\|\s*`(\w+)`\s*\|\s*([^|]+)\|/
default_rx = /\(\s*[Dd]efault:\s*`?\s*([^`]+)\s*`?\s*(\w+)?\)/

puts <<~HD
# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from decimal import Decimal
from typing import List, Optional
from .variable import Path, Variable
from .config import Config
HD

for line in config_str.split("\n")
    match = var_rx.match(line)
    if match.nil?
        next
    end
    name = match[1]
    description = match[2]
    if description.include?("Removed")
        next
    end
    description_lower = description.downcase
    type = "str"
    default = nil
    units = nil
    default_match = default_rx.match(description)
    if !default_match.nil?
        default = default_match[1]
        units = default_match[2]
        description = description.gsub(default_match[0], "")

        if default.downcase == "none" or default.downcase == "null"
            default = "None"
            type = "Optional[#{type}]"
        end
    end
    description.gsub!(/<br ?\/?>/, "")
    description.gsub!('"', '\"')
    description.strip!
    if not description.end_with?(".")
        description += "."
    end
    value_dec = nil
    begin
        value_dec = Rational(default)
    rescue => exception
    end
    if !value_dec.nil?
        type = "Decimal"
        if (
            description_lower.include?("enable") or
            description_lower.include?("allow")
        ) and (
            value_dec == 0 or
            value_dec == 1
        )
            type = "bool"
            if value_dec == 0
                default = "False"
            else
                default = "True"
            end
        end
    end
    if units.nil?
        if description.include?("in microns")
            units = "µm"
        end
    end
    if default == '""'
        default = '\"\"'
    end
    default_str = type.include?("str") ? "\"#{default}\"" : default
    default_line = default.nil? ? "default=None" : "default=#{default_str}"
    doc_units_line = units.nil? ? "doc_units=None" : "doc_units=\"#{units}\""
    puts <<~HD
    Variable(
        "#{name}",
        #{type},
        "#{description}",
        #{default_line},
        #{doc_units_line},
    ),
    HD

end