#!/usr/bin/env python3

import os
# import tempfile
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ParseError
from optparse import OptionParser
import logging

import common_utils
import configs
# import build_uce_tool
import cmd_help
import errors


def validate_args(gamelist_path, core_path, bios_dir, output_dir):
    if not gamelist_path or not core_path:
        logging.error('You must specify at least a path to a gamelist.xml and a path to a core')
        return False
    for dir_path in (bios_dir, output_dir):
        if dir_path:
            if not os.path.isdir(dir_path):
                logging.error(errors.invalid_path(dir_path, 'dir'))
                return False
    return True


def read_gamelist(gamelist_path):
    try:
        tree = ET.parse(gamelist_path)
    except ParseError:
        logging.error('{0} does not appear to be a valid XML file'.format(gamelist_path))
        return False
    return tree.getroot()


def parse_game_entry(game_entry):
    return {
        'name': game_entry.find('name').text,
        'rom_path': game_entry.find('path').text,
        'boxart_path': game_entry.find('thumbnail').text,
        'marquee': game_entry.find('marquee').text,
        'description': game_entry.find('desc').text
    }


def make_uce_sub_dirs(game_dir):
    for sub_dir in ('emu', 'roms', 'boxart', 'save'):
        common_utils.make_dir(os.path.join(game_dir, sub_dir))


def write_cart_xml(game_dir, game_name, game_desc):
    logging.info('Creating cartridge.xml file for {0}'.format(game_name))
    cart_xml = ''.join(configs.CARTRIDGE_XML)\
        .replace('GAME_TITLE', game_name)\
        .replace('GAME_DESCRIPTION', game_desc if game_desc else '')
    common_utils.write_file(os.path.join(game_dir, 'cartridge.xml'), cart_xml, 'w')


def write_exec_sh(game_dir, core_file_name, game_file_name):
    logging.info('Creating exec.sh for {0}'.format(game_file_name))
    exec_sh = ''.join(configs.EXEC_SH) \
        .replace('CORE_FILE_NAME', core_file_name) \
        .replace('GAME_FILE_NAME', game_file_name)
    common_utils.write_file(os.path.join(game_dir, 'exec.sh'), exec_sh, 'w')


def copy_dir_contents(source_dir, dest_dir):
    for file_name in os.listdir(source_dir):
        source_file_path = os.path.join(source_dir, file_name)
        if os.path.isfile(source_file_path):
            common_utils.copyfile(source_file_path, os.path.join(dest_dir, file_name))


def copy_source_files(core_path, bios_dir, game_data, game_dir):
    app_root = common_utils.get_app_root()
    box_art_target_path = os.path.join(game_dir, 'boxart', 'boxart.png')
    common_utils.copyfile(core_path, os.path.join(game_dir, 'emu', os.path.basename(core_path)))
    common_utils.copyfile(game_data['rom_path'], os.path.join(game_dir, 'roms', os.path.basename(game_data['rom_path'])))
    try:
        common_utils.copyfile(game_data['boxart_path'], box_art_target_path)
    except TypeError:
        logging.info('No boxart file found, using default')
        common_utils.copyfile(os.path.join(app_root, 'common', 'title.png'), box_art_target_path)
    if bios_dir:
        copy_dir_contents(bios_dir, os.path.join(game_dir, 'roms'))
    common_utils.create_symlink(box_art_target_path, os.path.join(game_dir, 'title.png'))


def setup_uce_source(core_path, bios_dir, game_data, game_dir):
    common_utils.make_dir(game_dir)
    make_uce_sub_dirs(game_dir)
    write_cart_xml(game_dir, game_data['name'], game_data['description'])
    write_exec_sh(game_dir, os.path.basename(core_path), os.path.basename(game_data['rom_path']))
    copy_source_files(core_path, bios_dir, game_data, game_dir)


# def build_uce(output_dir, game_dir):
#     target_path = os.path.join(output_dir, '{0}{1}'.format(os.path.basename(game_dir), '.UCE'))
#     build_uce_tool.main(game_dir, target_path)


# gamelist_path is only optional if a temp_dir containing a gamelist is passed in
def main(gamelist_path, core_path, bios_dir=None, output_dir=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s : %(message)s")
    output_dir = os.path.abspath(output_dir) if output_dir else os.path.join(os.path.split(os.path.abspath(gamelist_path))[0], 'recipes')
    common_utils.make_dir(output_dir)
    if not validate_args(gamelist_path, core_path, bios_dir, output_dir):
        return
    logging.info('Starting new recipes build run\n\n\n')
    common_utils.make_dir(output_dir)
    gamelist = read_gamelist(gamelist_path)
    if gamelist:
        for game_entry in gamelist:
            game_data = parse_game_entry(game_entry)
            game_dir = os.path.join(output_dir, os.path.splitext(os.path.basename(game_data['rom_path']))[0])
            setup_uce_source(core_path, bios_dir, game_data, game_dir)



def get_opts_parser():
    parser = OptionParser()
    parser.add_option('-g', '--gamelist', dest='gamelist_path', help=cmd_help.GAME_LIST, default=None)
    parser.add_option('-o', '--output', dest='output_dir', help=cmd_help.OUTPUT_DIR, default=None)
    parser.add_option('-c', '--core', dest='core_path', help=cmd_help.CORE, default=None)
    parser.add_option('-b', '--bios', dest='bios_dir', help=cmd_help.BIOS_DIR, default=None)
    return parser

# Check required options have been passed on the command line
# validate_args checks they make sense
# def validate_opts(parser):
#     (opts, args) = parser.parse_args()
#     valid = True
#     if opts.gamelist_path is None:
#         print(errors.NO_INPUT_GAMELIST)
#         valid = False
#     if opts.core_path is None:
#         print(errors.NO_CORE_FILE)
#         valid = False
#     if valid is False:
#         parser.print_help()
#         exit(0)
#     return opts, args


if __name__ == "__main__":
    parser = get_opts_parser()
    (opts, args) = parser.parse_args()

    main(opts.gamelist_path, opts.core_path, opts.bios_dir, opts.output_dir)

