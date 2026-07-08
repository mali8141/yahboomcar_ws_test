# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_M3Pro_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED M3Pro_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(M3Pro_FOUND FALSE)
  elseif(NOT M3Pro_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(M3Pro_FOUND FALSE)
  endif()
  return()
endif()
set(_M3Pro_CONFIG_INCLUDED TRUE)

# output package information
if(NOT M3Pro_FIND_QUIETLY)
  message(STATUS "Found M3Pro: 2.2.6 (${M3Pro_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'M3Pro' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${M3Pro_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(M3Pro_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${M3Pro_DIR}/${_extra}")
endforeach()
